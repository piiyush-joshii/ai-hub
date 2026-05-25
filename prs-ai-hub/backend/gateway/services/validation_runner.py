from datetime import datetime, timezone
from typing import Any

from orchestrator.graph import run_prs_validation_with_callbacks
from orchestrator.state import PRSState
from services.database import async_session, create_approval, log_agent_run, update_request_status
from services.run_context import new_run_id
from services.ws_manager import ws_manager


def build_initial_state(request_id: str, payload: dict[str, Any]) -> PRSState:
    requestor = payload.get("requestor", {})
    vendor = payload.get("vendor", {})
    need_by = requestor.get("need_by_date")
    if hasattr(need_by, "isoformat"):
        requestor = {**requestor, "need_by_date": need_by.isoformat()}

    return {
        "request_id": request_id,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "requestor_data": requestor,
        "vendor_data": vendor,
        "contract_text": payload.get("contract_text", ""),
        "contract_filename": payload.get("contract_filename", "contract.txt"),
        "sku_items": payload.get("sku_items", []),
        "addendum_text": payload.get("addendum_text", ""),
        "requestor_result": None,
        "vendor_result": None,
        "parties_result": None,
        "commercial_result": None,
        "legal_result": None,
        "sku_schedule_result": None,
        "sku_policy_result": None,
        "overall_status": None,
        "critical_blockers": [],
        "warnings": [],
        "requires_human_review": True,
        "next_action": None,
        "error": None,
    }


def build_orchestrator_result(final_state: PRSState) -> dict[str, Any]:
    return {
        "request_id": final_state["request_id"],
        "submitted_at": final_state["submitted_at"],
        "overall_status": final_state.get("overall_status", "fail"),
        "requires_human_review": final_state.get("requires_human_review", True),
        "agents": final_state.get("agents", {}),
        "critical_blockers": final_state.get("critical_blockers", []),
        "warnings": final_state.get("warnings", []),
        "next_action": final_state.get("next_action", ""),
        "review_time_estimate": final_state.get("review_time_estimate", "2-3 business days"),
        "agent_results": final_state.get("agent_results", {}),
    }


async def run_validation_job(request_id: str, payload: dict[str, Any]) -> None:
    run_id = new_run_id()

    async def on_agent_complete(agent_name: str, result: dict[str, Any]) -> None:
        async with async_session() as session:
            await log_agent_run(
                session,
                run_id=run_id,
                parent_ref=request_id,
                agent_name=agent_name,
                phase="prs",
                status="completed",
                result=result,
                output_status=result.get("status"),
            )
        await ws_manager.broadcast(
            request_id,
            {
                "event": "agent_complete",
                "agent": agent_name,
                "status": result.get("status", "unknown"),
            },
        )

    async with async_session() as session:
        await update_request_status(session, request_id, "processing")

    try:
        initial = build_initial_state(request_id, payload)
        final_state = await run_prs_validation_with_callbacks(initial, on_agent_complete)
        result = build_orchestrator_result(final_state)

        async with async_session() as session:
            await update_request_status(session, request_id, "complete", agent_results=result)
            if result.get("requires_human_review"):
                await create_approval(
                    session,
                    item_type="prs_submission",
                    ref_id=f"PRS-APPROVE-{request_id}",
                    title=f"PRS validation: {request_id} ({result.get('overall_status')})",
                    payload={"request_id": request_id, "overall_status": result.get("overall_status")},
                    agent_result=result,
                )

        await ws_manager.broadcast(
            request_id,
            {
                "event": "validation_complete",
                "overall_status": result["overall_status"],
                "result": result,
            },
        )
    except Exception as e:
        async with async_session() as session:
            await update_request_status(session, request_id, "failed", error=str(e))
        await ws_manager.broadcast(
            request_id,
            {"event": "validation_failed", "error": str(e)},
        )
