# ORCHESTRATOR.md — LangGraph Orchestrator Specification

> The orchestrator is the **brain** of the system.
> It runs as part of the Gateway service (no separate port needed).
> Uses LangGraph to define a state machine that fans out to all 7 agents in parallel.

---

## Dependencies

```bash
pip install langgraph langchain langchain-groq httpx
```

---

## Graph Overview

```
START
  │
  ▼
[validate_intake_request]      ← Basic schema validation before calling agents
  │
  ├──────────────────────────────────────────────┐
  │                                              │
  ▼                                              ▼
[run_requestor_agent]                    [run_vendor_agent]
  │                                              │
  └──────────────┬───────────────────────────────┘
                 ▼
         [intake_complete]     ← Gate: both intake agents done
                 │
  ┌──────────────┼──────────────────────────────┐
  │              │                              │
  ▼              ▼                              ▼
[run_parties_   [run_commercial_        [run_legal_
 definitions]    terms_agent]            clauses_agent]
  │              │                              │
  └──────────────┼──────────────────────────────┘
                 ▼
         [contract_complete]   ← Gate: all contract agents done
                 │
  ┌──────────────┘
  │
  ├──────────────────────────┐
  ▼                          ▼
[run_sku_schedule_agent]   [run_sku_policy_agent]
  │                          │
  └──────────┬───────────────┘
             ▼
       [sku_complete]         ← Gate: both SKU agents done
             │
             ▼
       [merge_results]        ← Combines all 7 agent outputs
             │
             ▼
       [determine_status]     ← pass / partial / fail + next_action
             │
             ▼
          [END]
```

---

## State Definition

```python
# orchestrator/state.py
from typing import TypedDict, Optional, Dict, Any, List
from datetime import datetime

class PRSState(TypedDict):
    # Input
    request_id: str
    submitted_at: str
    requestor_data: Dict[str, Any]
    vendor_data: Dict[str, Any]
    contract_text: str
    contract_filename: str
    sku_items: List[Dict[str, Any]]
    addendum_text: str

    # Agent outputs (populated as graph runs)
    requestor_result: Optional[Dict[str, Any]]
    vendor_result: Optional[Dict[str, Any]]
    parties_result: Optional[Dict[str, Any]]
    commercial_result: Optional[Dict[str, Any]]
    legal_result: Optional[Dict[str, Any]]
    sku_schedule_result: Optional[Dict[str, Any]]
    sku_policy_result: Optional[Dict[str, Any]]

    # Final output
    overall_status: Optional[str]
    critical_blockers: List[str]
    warnings: List[str]
    requires_human_review: bool
    next_action: Optional[str]
    error: Optional[str]
```

---

## Graph Implementation

```python
# orchestrator/graph.py
import asyncio
import httpx
from langgraph.graph import StateGraph, END
from orchestrator.state import PRSState
import os

INTAKE_URL = os.getenv("INTAKE_AGENT_URL", "http://localhost:8001")
CONTRACT_URL = os.getenv("CONTRACT_AGENT_URL", "http://localhost:8002")
SKU_URL = os.getenv("SKU_AGENT_URL", "http://localhost:8003")

# ── Node: Call Requestor Agent ──────────────────────────────
async def run_requestor_agent(state: PRSState) -> PRSState:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{INTAKE_URL}/agents/intake/requestor",
            json=state["requestor_data"]
        )
        state["requestor_result"] = response.json()
    return state

# ── Node: Call Vendor Agent ──────────────────────────────────
async def run_vendor_agent(state: PRSState) -> PRSState:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{INTAKE_URL}/agents/intake/vendor",
            json=state["vendor_data"]
        )
        state["vendor_result"] = response.json()
    return state

# ── Node: Call Parties & Definitions Agent ───────────────────
async def run_parties_agent(state: PRSState) -> PRSState:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{CONTRACT_URL}/agents/contract/parties",
            json={
                "request_id": state["request_id"],
                "contract_text": state["contract_text"],
                "contract_filename": state["contract_filename"]
            }
        )
        state["parties_result"] = response.json()
    return state

# ── Node: Call Commercial Terms Agent ───────────────────────
async def run_commercial_agent(state: PRSState) -> PRSState:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{CONTRACT_URL}/agents/contract/commercial",
            json={
                "request_id": state["request_id"],
                "contract_text": state["contract_text"],
                "contract_filename": state["contract_filename"]
            }
        )
        state["commercial_result"] = response.json()
    return state

# ── Node: Call Legal Clauses Agent ──────────────────────────
async def run_legal_agent(state: PRSState) -> PRSState:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{CONTRACT_URL}/agents/contract/legal",
            json={
                "request_id": state["request_id"],
                "contract_text": state["contract_text"],
                "contract_filename": state["contract_filename"]
            }
        )
        state["legal_result"] = response.json()
    return state

# ── Node: Call SKU Schedule Agent ───────────────────────────
async def run_sku_schedule_agent(state: PRSState) -> PRSState:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{SKU_URL}/agents/sku/schedule",
            json={
                "request_id": state["request_id"],
                "sku_items": state["sku_items"],
                "addendum_text": state["addendum_text"]
            }
        )
        state["sku_schedule_result"] = response.json()
    return state

# ── Node: Call SKU Policy Agent ──────────────────────────────
async def run_sku_policy_agent(state: PRSState) -> PRSState:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{SKU_URL}/agents/sku/policy",
            json={
                "request_id": state["request_id"],
                "addendum_text": state["addendum_text"]
            }
        )
        state["sku_policy_result"] = response.json()
    return state

# ── Node: Run intake agents in parallel ─────────────────────
async def run_intake_parallel(state: PRSState) -> PRSState:
    results = await asyncio.gather(
        run_requestor_agent(state),
        run_vendor_agent(state)
    )
    state["requestor_result"] = results[0]["requestor_result"]
    state["vendor_result"] = results[1]["vendor_result"]
    return state

# ── Node: Run contract agents in parallel ───────────────────
async def run_contract_parallel(state: PRSState) -> PRSState:
    results = await asyncio.gather(
        run_parties_agent(state),
        run_commercial_agent(state),
        run_legal_agent(state)
    )
    state["parties_result"] = results[0]["parties_result"]
    state["commercial_result"] = results[1]["commercial_result"]
    state["legal_result"] = results[2]["legal_result"]
    return state

# ── Node: Run SKU agents in parallel ────────────────────────
async def run_sku_parallel(state: PRSState) -> PRSState:
    results = await asyncio.gather(
        run_sku_schedule_agent(state),
        run_sku_policy_agent(state)
    )
    state["sku_schedule_result"] = results[0]["sku_schedule_result"]
    state["sku_policy_result"] = results[1]["sku_policy_result"]
    return state

# ── Node: Merge & determine final status ────────────────────
def merge_results(state: PRSState) -> PRSState:
    all_results = {
        "requestor_info": state.get("requestor_result", {}),
        "vendor_info": state.get("vendor_result", {}),
        "parties_and_definitions": state.get("parties_result", {}),
        "commercial_terms": state.get("commercial_result", {}),
        "legal_clauses": state.get("legal_result", {}),
        "sku_schedule": state.get("sku_schedule_result", {}),
        "sku_policy": state.get("sku_policy_result", {}),
    }

    agent_statuses = {k: v.get("status", "unknown") for k, v in all_results.items()}
    fail_count = sum(1 for s in agent_statuses.values() if s == "fail")
    partial_count = sum(1 for s in agent_statuses.values() if s == "partial")

    # Collect all critical blockers and warnings
    critical_blockers = []
    warnings = []
    for result in all_results.values():
        critical_blockers.extend(result.get("high_risk_flags", []))
        warnings.extend(result.get("medium_risk_flags", []))
        warnings.extend(result.get("warnings", []))

    # Determine overall status
    if fail_count > 0 or len(critical_blockers) > 0:
        overall_status = "fail"
        next_action = "Return to requestor for required corrections before legal review"
    elif partial_count > 0:
        overall_status = "partial"
        next_action = "Route to procurement team for manual review of incomplete sections"
    else:
        overall_status = "pass"
        next_action = "Route to legal team for final approval"

    state["overall_status"] = overall_status
    state["critical_blockers"] = critical_blockers
    state["warnings"] = warnings
    state["requires_human_review"] = overall_status != "pass"
    state["next_action"] = next_action

    return state

# ── Build the graph ──────────────────────────────────────────
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
```

---

## Invoking the Graph

```python
# In your FastAPI gateway endpoint:
from orchestrator.graph import prs_graph
from datetime import datetime, timezone
import uuid

async def run_prs_validation(payload: PRSFullRequest) -> OrchestratorResult:
    request_id = f"PRS-{datetime.now().strftime('%Y')}-{uuid.uuid4().hex[:8].upper()}"

    initial_state = {
        "request_id": request_id,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "requestor_data": payload.requestor.dict(),
        "vendor_data": payload.vendor.dict(),
        "contract_text": payload.contract_text,
        "contract_filename": payload.contract_filename,
        "sku_items": [item.dict() for item in payload.sku_items],
        "addendum_text": payload.addendum_text,
        # All result fields start as None
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

    final_state = await prs_graph.ainvoke(initial_state)
    return final_state
```

---

## Expected Execution Time

| Phase | Agents Running | Estimated Time |
|-------|---------------|----------------|
| Intake (parallel) | Requestor + Vendor | ~2-4 seconds |
| Contract (parallel) | Parties + Commercial + Legal | ~4-8 seconds |
| SKU (parallel) | Schedule + Policy | ~2-4 seconds |
| Merge | — | <0.1 seconds |
| **Total** | **7 agents** | **~8-16 seconds** |

> Groq's fast inference keeps total wall-clock time low even with 7 LLM calls.
