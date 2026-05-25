"""Phase 0/1 pilot — batch intake, approvals, supplier drafts, run logs."""
import os
import time

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.database import (
    async_session,
    create_approval,
    decide_approval,
    list_approvals,
    list_run_logs,
    log_agent_run,
)
from services.enterprise_data import (
    get_intake_submission,
    get_supplier_message,
    intake_submission_key,
    load_intake_submissions,
    load_intake_validation_rules,
    load_supplier_messages,
)
from services.run_context import new_run_id

router = APIRouter()

INTAKE_AGENT_URL = os.getenv("INTAKE_AGENT_URL", "http://localhost:8001")
SUPPLIER_AGENT_URL = os.getenv("SUPPLIER_AGENT_URL", "http://localhost:8005")


@router.get("/status")
async def pilot_status():
    return {
        "phase": "1-pilot",
        "capabilities": [
            "batch_intake_validation",
            "supplier_message_compose",
            "approval_queue",
            "agent_run_logs",
        ],
        "data_source": "data/enterprise/*.json (sync via scripts/sync_enterprise_data.py)",
    }


@router.get("/intake/submissions")
async def list_intake_submissions():
    rows = load_intake_submissions()
    return {
        "items": [{**r, "submission_key": intake_submission_key(r)} for r in rows],
        "total": len(rows),
    }


@router.post("/intake/submissions/{submission_key}/validate")
async def validate_intake_submission(submission_key: str):
    row = get_intake_submission(submission_key)
    if not row:
        raise HTTPException(status_code=404, detail="Submission not found")

    run_id = new_run_id()
    rules = load_intake_validation_rules()
    payload = {"submission": row, "validation_rules": rules}
    started = time.perf_counter()

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(f"{INTAKE_AGENT_URL}/agents/intake/vizient", json=payload)
        if response.is_error:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except Exception:
                pass
            async with async_session() as session:
                await log_agent_run(
                    session,
                    run_id=run_id,
                    parent_ref=submission_key,
                    agent_name="prs_intake_vizient",
                    phase="pilot_intake",
                    status="failed",
                    error=str(detail),
                    latency_ms=int((time.perf_counter() - started) * 1000),
                )
            raise HTTPException(status_code=response.status_code, detail=str(detail))
        result = response.json()

    latency = int((time.perf_counter() - started) * 1000)
    async with async_session() as session:
        await log_agent_run(
            session,
            run_id=run_id,
            parent_ref=submission_key,
            agent_name="prs_intake_vizient",
            phase="pilot_intake",
            status="completed",
            result=result,
            output_status=result.get("status"),
            latency_ms=latency,
        )
        if result.get("status") in ("fail", "partial") or not result.get("ready_to_progress", True):
            await create_approval(
                session,
                item_type="intake_submission",
                ref_id=f"INTAKE-{submission_key}",
                title=f"Intake review: {submission_key}",
                payload=row,
                agent_result=result,
            )

    return {"submission_key": submission_key, "run_id": run_id, "result": result}


@router.get("/supplier/messages")
async def list_supplier_messages_queue():
    messages = load_supplier_messages()
    return {"items": messages, "total": len(messages)}


@router.post("/supplier/messages/{message_id}/compose")
async def compose_supplier_message(message_id: str):
    msg = get_supplier_message(message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    run_id = new_run_id()
    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{SUPPLIER_AGENT_URL}/agents/supplier/compose",
            json={"message": msg, "template_hint": msg.get("template_id", "")},
        )
        if response.is_error:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except Exception:
                pass
            raise HTTPException(status_code=response.status_code, detail=str(detail))
        result = response.json()

    latency = int((time.perf_counter() - started) * 1000)
    async with async_session() as session:
        await log_agent_run(
            session,
            run_id=run_id,
            parent_ref=message_id,
            agent_name="supplier_interaction",
            phase="pilot_supplier",
            status="completed",
            result=result,
            output_status=result.get("status"),
            latency_ms=latency,
        )
        if result.get("requires_human_approval", True) or msg.get("human_approval_required") == "YES":
            await create_approval(
                session,
                item_type="supplier_message",
                ref_id=f"MSG-APPROVE-{message_id}",
                title=f"Supplier email: {message_id} — {msg.get('supplier_name', '')}",
                payload=msg,
                agent_result=result,
            )

    return {"message_id": message_id, "run_id": run_id, "draft": result}


@router.get("/approvals")
async def list_pending_approvals():
    async with async_session() as session:
        items = await list_approvals(session, status="pending")
    return {
        "items": [
            {
                "ref_id": i.ref_id,
                "item_type": i.item_type,
                "title": i.title,
                "status": i.status,
                "payload": i.payload,
                "agent_result": i.agent_result,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ],
        "total": len(items),
    }


class ApprovalDecision(BaseModel):
    note: str | None = None
    decided_by: str = "operator"


@router.post("/approvals/{ref_id}/approve")
async def approve_item(ref_id: str, body: ApprovalDecision):
    async with async_session() as session:
        row = await decide_approval(session, ref_id, "approved", body.decided_by, body.note)
    if not row:
        raise HTTPException(status_code=404, detail="Approval item not found")
    return {"ref_id": ref_id, "status": "approved"}


@router.post("/approvals/{ref_id}/reject")
async def reject_item(ref_id: str, body: ApprovalDecision):
    async with async_session() as session:
        row = await decide_approval(session, ref_id, "rejected", body.decided_by, body.note)
    if not row:
        raise HTTPException(status_code=404, detail="Approval item not found")
    return {"ref_id": ref_id, "status": "rejected"}


@router.get("/runs")
async def list_agent_runs(parent_ref: str | None = None, limit: int = 50):
    async with async_session() as session:
        logs = await list_run_logs(session, parent_ref=parent_ref, limit=limit)
    return {
        "items": [
            {
                "run_id": l.run_id,
                "parent_ref": l.parent_ref,
                "agent_name": l.agent_name,
                "phase": l.phase,
                "status": l.status,
                "output_status": l.output_status,
                "latency_ms": l.latency_ms,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
        "total": len(logs),
    }
