import os
import time

import httpx
from fastapi import APIRouter, HTTPException

from services.database import async_session, create_approval, log_agent_run
from services.enterprise_data import (
    get_transaction,
    load_transactions,
    resolve_contract_text,
)
from services.run_context import new_run_id

router = APIRouter()

CCR_AGENT_URL = os.getenv("CCR_AGENT_URL", "http://localhost:8004")


@router.get("/transactions")
async def list_ccr_transactions():
    items = load_transactions()
    return {
        "items": items,
        "total": len(items),
        "source": "ccr_decision_input_may2026.xlsx (synced to data/enterprise/)",
    }


@router.get("/transactions/{transaction_id}")
async def get_ccr_transaction(transaction_id: str):
    txn = get_transaction(transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    filename, text = resolve_contract_text(txn.get("contract_number", ""))
    return {"transaction": txn, "contract_filename": filename, "contract_char_count": len(text)}


@router.post("/transactions/{transaction_id}/evaluate")
async def evaluate_ccr_transaction(transaction_id: str):
    txn = get_transaction(transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    filename, contract_text = resolve_contract_text(txn.get("contract_number", ""))
    payload = {
        "transaction_id": transaction_id,
        "transaction": txn,
        "contract_text": contract_text,
        "contract_filename": filename,
    }

    run_id = new_run_id()
    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(f"{CCR_AGENT_URL}/agents/ccr/decide", json=payload)
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
            parent_ref=transaction_id,
            agent_name="ccr_decision",
            phase="ccr",
            status="completed",
            result=result,
            output_status=result.get("ccr_decision") or result.get("status"),
            latency_ms=latency,
        )
        if result.get("requires_human_approval") or result.get("ccr_decision") == "HARD_EXCEPTION":
            await create_approval(
                session,
                item_type="ccr_decision",
                ref_id=f"CCR-APPROVE-{transaction_id}",
                title=f"CCR: {transaction_id} — {result.get('ccr_decision', 'review')}",
                payload=txn,
                agent_result=result,
            )

    expected = txn.get("expected_ccr_decision") or ""
    actual = result.get("ccr_decision", "")
    return {
        "transaction_id": transaction_id,
        "expected_ccr_decision": expected,
        "matches_expected": bool(expected and actual and expected.upper() == actual.upper()),
        "contract_number": txn.get("contract_number"),
        "contract_filename": filename,
        "result": result,
    }
