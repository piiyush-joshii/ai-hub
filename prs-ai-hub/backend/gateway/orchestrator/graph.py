import asyncio
import os
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from langgraph.graph import END, StateGraph

from orchestrator.state import PRSState

INTAKE_URL = os.getenv("INTAKE_AGENT_URL", "http://localhost:8001")
CONTRACT_URL = os.getenv("CONTRACT_AGENT_URL", "http://localhost:8002")
SKU_URL = os.getenv("SKU_AGENT_URL", "http://localhost:8003")

AgentCallback = Callable[[str, dict[str, Any]], Awaitable[None]]


async def _post(client: httpx.AsyncClient, url: str, payload: dict) -> dict:
    response = await client.post(url, json=payload)
    if response.is_error:
        detail = response.text
        try:
            body = response.json()
            if isinstance(body, dict) and "detail" in body:
                detail = body["detail"]
        except Exception:
            pass
        raise RuntimeError(f"Agent call failed ({response.status_code}): {detail}") from None
    return response.json()


async def run_requestor_agent(state: PRSState) -> PRSState:
    async with httpx.AsyncClient(timeout=60) as client:
        result = await _post(
            client, f"{INTAKE_URL}/agents/intake/requestor", state["requestor_data"]
        )
    return {**state, "requestor_result": result}


async def run_vendor_agent(state: PRSState) -> PRSState:
    async with httpx.AsyncClient(timeout=60) as client:
        result = await _post(client, f"{INTAKE_URL}/agents/intake/vendor", state["vendor_data"])
    return {**state, "vendor_result": result}


async def run_parties_agent(state: PRSState) -> PRSState:
    payload = {
        "request_id": state["request_id"],
        "contract_text": state["contract_text"],
        "contract_filename": state["contract_filename"],
    }
    async with httpx.AsyncClient(timeout=90) as client:
        result = await _post(client, f"{CONTRACT_URL}/agents/contract/parties", payload)
    return {**state, "parties_result": result}


async def run_commercial_agent(state: PRSState) -> PRSState:
    payload = {
        "request_id": state["request_id"],
        "contract_text": state["contract_text"],
        "contract_filename": state["contract_filename"],
    }
    async with httpx.AsyncClient(timeout=90) as client:
        result = await _post(client, f"{CONTRACT_URL}/agents/contract/commercial", payload)
    return {**state, "commercial_result": result}


async def run_legal_agent(state: PRSState) -> PRSState:
    payload = {
        "request_id": state["request_id"],
        "contract_text": state["contract_text"],
        "contract_filename": state["contract_filename"],
    }
    async with httpx.AsyncClient(timeout=90) as client:
        result = await _post(client, f"{CONTRACT_URL}/agents/contract/legal", payload)
    return {**state, "legal_result": result}


async def run_sku_schedule_agent(state: PRSState) -> PRSState:
    payload = {
        "request_id": state["request_id"],
        "sku_items": state["sku_items"],
        "addendum_text": state["addendum_text"],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        result = await _post(client, f"{SKU_URL}/agents/sku/schedule", payload)
    return {**state, "sku_schedule_result": result}


async def run_sku_policy_agent(state: PRSState) -> PRSState:
    payload = {
        "request_id": state["request_id"],
        "addendum_text": state["addendum_text"],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        result = await _post(client, f"{SKU_URL}/agents/sku/policy", payload)
    return {**state, "sku_policy_result": result}


async def run_intake_parallel(state: PRSState) -> PRSState:
    r1, r2 = await asyncio.gather(run_requestor_agent(state), run_vendor_agent(state))
    merged = {**state}
    merged["requestor_result"] = r1["requestor_result"]
    merged["vendor_result"] = r2["vendor_result"]
    return merged


async def run_contract_parallel(state: PRSState) -> PRSState:
    # Run sequentially to avoid Groq rate limits on parallel contract calls.
    state = await run_parties_agent(state)
    state = await run_commercial_agent(state)
    state = await run_legal_agent(state)
    return state


async def run_sku_parallel(state: PRSState) -> PRSState:
    r1, r2 = await asyncio.gather(run_sku_schedule_agent(state), run_sku_policy_agent(state))
    merged = {**state}
    merged["sku_schedule_result"] = r1["sku_schedule_result"]
    merged["sku_policy_result"] = r2["sku_policy_result"]
    return merged


def merge_results(state: PRSState) -> PRSState:
    all_results = {
        "requestor_info": state.get("requestor_result") or {},
        "vendor_info": state.get("vendor_result") or {},
        "parties_and_definitions": state.get("parties_result") or {},
        "commercial_terms": state.get("commercial_result") or {},
        "legal_clauses": state.get("legal_result") or {},
        "sku_schedule": state.get("sku_schedule_result") or {},
        "sku_policy": state.get("sku_policy_result") or {},
    }

    agent_statuses = {k: (v.get("status") or "unknown") for k, v in all_results.items()}
    fail_count = sum(1 for s in agent_statuses.values() if s == "fail")
    partial_count = sum(1 for s in agent_statuses.values() if s == "partial")

    critical_blockers: list[str] = []
    warnings: list[str] = []

    for result in all_results.values():
        critical_blockers.extend(result.get("high_risk_flags", []))
        for flag in result.get("risk_flags", []):
            if isinstance(flag, str):
                warnings.append(flag)
        warnings.extend(result.get("medium_risk_flags", []))
        warnings.extend(result.get("warnings", []))

    if fail_count > 0 or len(critical_blockers) > 0:
        overall_status = "fail"
        next_action = "Return to requestor for required corrections before legal review"
        review_time = "3-5 business days"
    elif partial_count > 0:
        overall_status = "partial"
        next_action = "Route to procurement team for manual review of incomplete sections"
        review_time = "2-3 business days"
    else:
        overall_status = "pass"
        next_action = "Route to legal team for final approval"
        review_time = "1-2 business days"

    return {
        **state,
        "overall_status": overall_status,
        "agents": agent_statuses,
        "critical_blockers": critical_blockers,
        "warnings": warnings,
        "requires_human_review": overall_status != "pass",
        "next_action": next_action,
        "review_time_estimate": review_time,
        "agent_results": all_results,
    }


def build_prs_graph():
    graph = StateGraph(PRSState)
    graph.add_node("run_intake", run_intake_parallel)
    graph.add_node("run_contract", run_contract_parallel)
    graph.add_node("run_sku", run_sku_parallel)
    graph.add_node("merge_results", merge_results)
    graph.set_entry_point("run_intake")
    graph.add_edge("run_intake", "run_contract")
    graph.add_edge("run_contract", "run_sku")
    graph.add_edge("run_sku", "merge_results")
    graph.add_edge("merge_results", END)
    return graph.compile()


prs_graph = build_prs_graph()

AGENT_KEYS = [
    ("requestor_info", "requestor_result"),
    ("vendor_info", "vendor_result"),
    ("parties_and_definitions", "parties_result"),
    ("commercial_terms", "commercial_result"),
    ("legal_clauses", "legal_result"),
    ("sku_schedule", "sku_schedule_result"),
    ("sku_policy", "sku_policy_result"),
]


async def run_prs_validation_with_callbacks(
    initial_state: PRSState,
    on_agent_complete: AgentCallback | None = None,
) -> PRSState:
    """Run validation sequentially by phase with optional progress callbacks."""
    state: PRSState = dict(initial_state)

    state = await run_intake_parallel(state)
    if on_agent_complete:
        if state.get("requestor_result"):
            await on_agent_complete("requestor_info", state["requestor_result"])
        if state.get("vendor_result"):
            await on_agent_complete("vendor_info", state["vendor_result"])

    state = await run_contract_parallel(state)
    if on_agent_complete:
        if state.get("parties_result"):
            await on_agent_complete("parties_and_definitions", state["parties_result"])
        if state.get("commercial_result"):
            await on_agent_complete("commercial_terms", state["commercial_result"])
        if state.get("legal_result"):
            await on_agent_complete("legal_clauses", state["legal_result"])

    state = await run_sku_parallel(state)
    if on_agent_complete:
        if state.get("sku_schedule_result"):
            await on_agent_complete("sku_schedule", state["sku_schedule_result"])
        if state.get("sku_policy_result"):
            await on_agent_complete("sku_policy", state["sku_policy_result"])

    state = merge_results(state)
    return state
