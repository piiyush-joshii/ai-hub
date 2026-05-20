#!/usr/bin/env python3
"""Sync all enterprise xlsx test data into JSON for the Enterprise explorer UI."""
from __future__ import annotations

import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DATA = ROOT.parent / "data"
OUT_DIR = ROOT / "data" / "enterprise"

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

HEADER_MARKERS = frozenset(
    {
        "transaction_id",
        "invoice_id",
        "exception_id",
        "workflow_id",
        "message_id",
        "feedback_id",
        "supplier_id",
        "payment_id",
        "handoff_id",
        "row",
        "field",
    }
)

CONTRACT_FILE_BY_NUMBER = {
    "C-2024-001": "C-2024-001_apextech_supply.txt",
    "C-2023-029": "C-2023-029_vertex_ambiguous.txt",
    "C-2023-015": "C-2023-015_stratagem_services.txt",
    "C-2022-008": "C-2022-008_primeservice_facilities.txt",
    "C-2019-003": "C-2019-003_vortex_expired.txt",
    "C-2024-021": "C-2024-001_apextech_supply.txt",
    "C-2023-061": "C-2023-029_vertex_ambiguous.txt",
    "C-2023-052": "C-2023-015_stratagem_services.txt",
    "C-2023-044": "C-2024-001_apextech_supply.txt",
    "C-2023-077": "C-2022-008_primeservice_facilities.txt",
}


def _norm_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _to_snake_record(raw: dict[str, str]) -> dict:
    return {_norm_key(k): v for k, v in raw.items() if str(v).strip()}


def _shared_strings(z: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    out = []
    for si in root.findall(".//m:si", NS):
        out.append("".join((t.text or "") for t in si.findall(".//m:t", NS)))
    return out


def _col_idx(ref: str) -> int:
    m = re.match(r"([A-Z]+)", ref)
    col_s = m.group(1) if m else "A"
    col = 0
    for ch in col_s:
        col = col * 26 + ord(ch) - 64
    return col


def _cell_text(c: ET.Element, ss: list[str]) -> str:
    t = c.get("t")
    if t == "inlineStr":
        is_el = c.find("m:is", NS)
        if is_el is not None:
            return "".join((x.text or "") for x in is_el.findall(".//m:t", NS))
    v = c.find("m:v", NS)
    if v is None or v.text is None:
        return ""
    if t == "s":
        idx = int(v.text)
        return ss[idx] if idx < len(ss) else ""
    return v.text


def _sheet_grid(z: zipfile.ZipFile, sheet_index: int) -> dict[int, dict[int, str]]:
    ss = _shared_strings(z)
    root = ET.fromstring(z.read(f"xl/worksheets/sheet{sheet_index}.xml"))
    grid: dict[int, dict[int, str]] = {}
    for row in root.findall(".//m:sheetData/m:row", NS):
        ridx = int(row.get("r", 0))
        line: dict[int, str] = {}
        for c in row.findall("m:c", NS):
            line[_col_idx(c.get("r", ""))] = _cell_text(c, ss)
        if line:
            grid[ridx] = line
    return grid


def _find_header_row(grid: dict[int, dict[int, str]]) -> int | None:
    for ridx in sorted(grid):
        for val in grid[ridx].values():
            if _norm_key(val) in HEADER_MARKERS:
                return ridx
    return None


def read_sheet_records(path: Path, sheet_index: int) -> list[dict]:
    with zipfile.ZipFile(path) as z:
        grid = _sheet_grid(z, sheet_index)
    header_row = _find_header_row(grid)
    if header_row is None:
        return []

    headers = grid[header_row]
    col_to_name = {col: headers[col].strip() for col in headers if headers[col].strip()}
    records: list[dict] = []
    for ridx in sorted(grid):
        if ridx <= header_row:
            continue
        row = grid[ridx]
        if not any(str(v).strip() for v in row.values()):
            continue
        raw: dict[str, str] = {}
        for col, name in col_to_name.items():
            val = row.get(col, "")
            if val is not None and str(val).strip():
                raw[name] = str(val).strip()
        snake = _to_snake_record(raw)
        if len(snake) < 2:
            continue
        first_val = next(iter(snake.values()), "").lower()
        if "legend" in first_val or "colour" in first_val:
            continue
        records.append(snake)
    return records


def _parse_float(val: str | None) -> float | None:
    if not val:
        return None
    try:
        return float(str(val).replace(",", "").replace("$", ""))
    except ValueError:
        return None


def normalize_transaction(raw: dict[str, str]) -> dict:
    contract = raw.get("contract_number", "")
    return {
        **raw,
        "invoice_amount_usd": _parse_float(raw.get("invoice_amount_usd")),
        "prs_completeness_score": _parse_float(raw.get("prs_completeness_score")),
        "contract_value_usd": _parse_float(
            raw.get("contract_value_usd") or raw.get("contract_total_value_usd")
        ),
        "contract_ceiling_monthly_usd": _parse_float(
            raw.get("contract_ceiling_monthly_usd") or raw.get("approved_monthly_ceiling_usd")
        ),
        "contract_filename": CONTRACT_FILE_BY_NUMBER.get(contract),
    }


def sync_ccr() -> int:
    path = SOURCE_DATA / "ccr_decision_input_may2026.xlsx"
    rows = read_sheet_records(path, 1)
    transactions = [
        normalize_transaction(r)
        for r in rows
        if r.get("transaction_id", "").startswith("TXN-")
    ]
    scenarios = [
        r
        for r in read_sheet_records(path, 2)
        if r.get("transaction_id", "").startswith("TXN-")
    ]
    by_id = {s["transaction_id"]: s for s in scenarios}
    for txn in transactions:
        ref = by_id.get(txn["transaction_id"])
        if ref:
            txn["expected_ccr_decision"] = (
                ref.get("expected_ccr_output")
                or txn.get("prior_ccr_decision", "")
                or txn.get("expected_ccr_decision", "")
            )
            txn["scenario_description"] = ref.get("scenario", "")
    _write("ccr_transactions.json", {"transactions": transactions, "source": path.name})
    _write("ccr_scenarios.json", {"records": scenarios, "source": path.name})
    return len(transactions)


def sync_vizient_intake() -> tuple[int, int, int]:
    path = SOURCE_DATA / "vizient_prs_intake_agent_may0519.xlsx"
    subs = [r for r in read_sheet_records(path, 1) if r.get("supplier_id", "").startswith("VZ-")]
    issues = read_sheet_records(path, 2)
    rules = read_sheet_records(path, 3)
    _write("intake_submissions.json", {"records": subs, "source": path.name})
    _write("intake_known_issues.json", {"records": issues, "source": path.name})
    _write("intake_validation_rules.json", {"records": rules, "source": path.name})
    return len(subs), len(issues), len(rules)


def sync_orchestrator() -> tuple[int, int, int]:
    path = SOURCE_DATA / "orchestrator_workflow_inputFile_0519.xlsx"
    active = [r for r in read_sheet_records(path, 1) if r.get("workflow_id", "").startswith("WF-")]
    handoffs = [r for r in read_sheet_records(path, 2) if r.get("handoff_id", "").startswith("HO-")]
    sla = [r for r in read_sheet_records(path, 3) if r.get("workflow_id", "").startswith("WF-")]
    _write("workflows_active.json", {"records": active, "source": path.name})
    _write("workflows_handoffs.json", {"records": handoffs, "source": path.name})
    _write("workflows_sla.json", {"records": sla, "source": path.name})
    return len(active), len(handoffs), len(sla)


def sync_cash_recon() -> tuple[int, int]:
    path = SOURCE_DATA / "Cash_reconciliation_input_0519.xlsx"
    invoices = [r for r in read_sheet_records(path, 1) if r.get("invoice_id", "").startswith("EXP-")]
    payments = [r for r in read_sheet_records(path, 2) if r.get("payment_id", "").startswith("PAY-")]
    patterns = [r for r in read_sheet_records(path, 3) if r.get("supplier_id", "").startswith("SUP-")]
    scenarios = read_sheet_records(path, 4)
    _write("cash_invoices.json", {"records": invoices, "source": path.name})
    _write("cash_payments.json", {"records": payments, "source": path.name})
    _write("cash_supplier_patterns.json", {"records": patterns, "source": path.name})
    _write("cash_scenarios.json", {"records": scenarios, "source": path.name})
    return len(invoices), len(payments)


def sync_exceptions() -> int:
    path = SOURCE_DATA / "exception_resolution_inputFile_0519.xlsx"
    queue = [r for r in read_sheet_records(path, 1) if r.get("exception_id", "").startswith("EXC-")]
    recovery = [r for r in read_sheet_records(path, 2) if r.get("exception_id", "").startswith("EXC-")]
    _write("exceptions_queue.json", {"records": queue, "source": path.name})
    _write("exceptions_recovery.json", {"records": recovery, "source": path.name})
    return len(queue)


def sync_supplier_comms() -> int:
    path = SOURCE_DATA / "supplier_interaction_inputFile_0519.xlsx"
    messages = [r for r in read_sheet_records(path, 1) if r.get("message_id", "").startswith("MSG-")]
    dialogue = [r for r in read_sheet_records(path, 2) if r.get("supplier_id", "").startswith("SUP-")]
    templates = read_sheet_records(path, 3)
    _write("supplier_messages.json", {"records": messages, "source": path.name})
    _write("supplier_dialogue.json", {"records": dialogue, "source": path.name})
    _write("supplier_templates.json", {"records": templates, "source": path.name})
    return len(messages)


def sync_learning() -> int:
    path = SOURCE_DATA / "learning_evaluation_InputFile_0519.xlsx"
    corrections = [r for r in read_sheet_records(path, 1) if r.get("feedback_id", "").startswith("LRN-")]
    refinements = [r for r in read_sheet_records(path, 2) if r.get("feedback_id", "").startswith("LRN-")]
    _write("learning_corrections.json", {"records": corrections, "source": path.name})
    _write("learning_refinements.json", {"records": refinements, "source": path.name})
    return len(corrections)


def _write(name: str, payload: dict) -> None:
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_manifest(counts: dict[str, int]) -> dict:
    return {
        "description": "Enterprise test datasets synced from ai-hub/data/*.xlsx",
        "pipeline_order": [
            "intake_submissions",
            "ccr_transactions",
            "cash_invoices",
            "exceptions_queue",
            "supplier_messages",
            "workflows_active",
            "learning_corrections",
        ],
        "datasets": [
            {
                "id": "intake_submissions",
                "label": "Vizient intake — submissions",
                "agent": "PRS Intake Agent",
                "source_file": "vizient_prs_intake_agent_may0519.xlsx",
                "count": counts.get("intake", 0),
                "use": "Validate monthly supplier invoice rows (Agent 1 rules).",
                "action": "Future: batch intake validation UI",
            },
            {
                "id": "intake_known_issues",
                "label": "Vizient intake — known issues",
                "agent": "PRS Intake Agent",
                "source_file": "vizient_prs_intake_agent_may0519.xlsx",
                "count": counts.get("intake_issues", 0),
                "use": "Test rows with injected validation defects.",
            },
            {
                "id": "intake_validation_rules",
                "label": "Vizient intake — US rules",
                "agent": "PRS Intake Agent",
                "source_file": "vizient_prs_intake_agent_may0519.xlsx",
                "count": counts.get("intake_rules", 0),
                "use": "Reference rule catalog (CR-01, CR-02, …).",
            },
            {
                "id": "ccr_transactions",
                "label": "CCR evaluation batch",
                "agent": "CCR Decision Agent",
                "source_file": "ccr_decision_input_may2026.xlsx",
                "count": counts.get("ccr", 0),
                "use": "Per-invoice decision vs contract terms.",
                "action": "Live: /ccr → Evaluate",
            },
            {
                "id": "workflows_active",
                "label": "Orchestrator — active workflows",
                "agent": "Workflow Orchestrator",
                "source_file": "orchestrator_workflow_inputFile_0519.xlsx",
                "count": counts.get("workflows", 0),
                "use": "Stage tracking per supplier/period (PRS→CIA→CCR→Cash).",
            },
            {
                "id": "workflows_handoffs",
                "label": "Orchestrator — handoffs",
                "agent": "Workflow Orchestrator",
                "source_file": "orchestrator_workflow_inputFile_0519.xlsx",
                "count": counts.get("handoffs", 0),
                "use": "Agent-to-agent payloads ready to dispatch.",
            },
            {
                "id": "workflows_sla",
                "label": "Orchestrator — SLA monitor",
                "agent": "Workflow Orchestrator",
                "source_file": "orchestrator_workflow_inputFile_0519.xlsx",
                "count": counts.get("sla", 0),
                "use": "Deadline breaches and orchestrator actions.",
            },
            {
                "id": "cash_invoices",
                "label": "Cash recon — candidate invoices",
                "agent": "Cash Reconciliation Agent",
                "source_file": "Cash_reconciliation_input_0519.xlsx",
                "count": counts.get("cash_inv", 0),
                "use": "Invoices after CCR PASS_THROUGH.",
            },
            {
                "id": "cash_payments",
                "label": "Cash recon — bank payments",
                "agent": "Cash Reconciliation Agent",
                "source_file": "Cash_reconciliation_input_0519.xlsx",
                "count": counts.get("cash_pay", 0),
                "use": "Incoming cash to match against invoices.",
            },
            {
                "id": "exceptions_queue",
                "label": "Exception resolution — queue",
                "agent": "Exception Resolution Agent",
                "source_file": "exception_resolution_inputFile_0519.xlsx",
                "count": counts.get("exceptions", 0),
                "use": "Open exceptions from any upstream failure.",
            },
            {
                "id": "supplier_messages",
                "label": "Supplier interaction — message queue",
                "agent": "Supplier Interaction Agent",
                "source_file": "supplier_interaction_inputFile_0519.xlsx",
                "count": counts.get("messages", 0),
                "use": "Outbound correction/ETA emails to suppliers.",
            },
            {
                "id": "learning_corrections",
                "label": "Learning — human overrides",
                "agent": "Learning / Evaluation",
                "source_file": "learning_evaluation_InputFile_0519.xlsx",
                "count": counts.get("learning", 0),
                "use": "Feedback to refine prompts and rules (offline).",
            },
        ],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    intake_n, intake_issues_n, intake_rules_n = sync_vizient_intake()
    wf_n, ho_n, sla_n = sync_orchestrator()
    cash_inv_n, cash_pay_n = sync_cash_recon()
    counts = {
        "ccr": sync_ccr(),
        "intake": intake_n,
        "intake_issues": intake_issues_n,
        "intake_rules": intake_rules_n,
        "workflows": wf_n,
        "handoffs": ho_n,
        "sla": sla_n,
        "cash_inv": cash_inv_n,
        "cash_pay": cash_pay_n,
        "exceptions": sync_exceptions(),
        "messages": sync_supplier_comms(),
        "learning": sync_learning(),
    }
    _write("manifest.json", build_manifest(counts))
    print("Enterprise sync complete:", counts)


if __name__ == "__main__":
    main()
