"""Load enterprise CCR transaction JSON and resolve contract text files."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_ENTERPRISE_DIR = _ROOT / "data" / "enterprise"
_CONTRACT_DIR = Path(
    os.getenv(
        "CONTRACT_INTELLIGENCE_DIR",
        str(_ROOT.parent / "data" / "Contract intelligence"),
    )
)

CONTRACT_FILE_BY_NUMBER: dict[str, str] = {
    "C-2024-001": "C-2024-001_apextech_supply.txt",
    "C-2023-029": "C-2023-029_vertex_ambiguous.txt",
    "C-2023-015": "C-2023-015_stratagem_services.txt",
    "C-2022-008": "C-2022-008_primeservice_facilities.txt",
    "C-2019-003": "C-2019-003_vortex_expired.txt",
}


def _load_json(name: str) -> dict:
    path = _ENTERPRISE_DIR / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_manifest() -> dict:
    return _load_json("manifest.json")


@lru_cache(maxsize=1)
def load_dataset(dataset_id: str) -> dict:
    mapping = {
        "intake_submissions": "intake_submissions.json",
        "intake_known_issues": "intake_known_issues.json",
        "intake_validation_rules": "intake_validation_rules.json",
        "ccr_transactions": "ccr_transactions.json",
        "workflows_active": "workflows_active.json",
        "workflows_handoffs": "workflows_handoffs.json",
        "workflows_sla": "workflows_sla.json",
        "cash_invoices": "cash_invoices.json",
        "cash_payments": "cash_payments.json",
        "cash_supplier_patterns": "cash_supplier_patterns.json",
        "cash_scenarios": "cash_scenarios.json",
        "exceptions_queue": "exceptions_queue.json",
        "exceptions_recovery": "exceptions_recovery.json",
        "supplier_messages": "supplier_messages.json",
        "supplier_dialogue": "supplier_dialogue.json",
        "supplier_templates": "supplier_templates.json",
        "learning_corrections": "learning_corrections.json",
        "learning_refinements": "learning_refinements.json",
    }
    filename = mapping.get(dataset_id)
    if not filename:
        return {}
    return _load_json(filename)


@lru_cache(maxsize=1)
def load_transactions() -> list[dict]:
    data = _load_json("ccr_transactions.json")
    return data.get("transactions", [])


def get_transaction(transaction_id: str) -> dict | None:
    for txn in load_transactions():
        if txn.get("transaction_id") == transaction_id:
            return txn
    return None


@lru_cache(maxsize=1)
def load_intake_submissions() -> list[dict]:
    data = _load_json("intake_submissions.json")
    return data.get("records", [])


@lru_cache(maxsize=1)
def load_intake_validation_rules() -> list[dict]:
    data = _load_json("intake_validation_rules.json")
    return data.get("records", [])


def intake_submission_key(row: dict) -> str:
    return f"{row.get('supplier_id', '')}:{row.get('invoice_number', '')}"


def get_intake_submission(submission_key: str) -> dict | None:
    for row in load_intake_submissions():
        if intake_submission_key(row) == submission_key:
            return row
    return None


@lru_cache(maxsize=1)
def load_supplier_messages() -> list[dict]:
    data = _load_json("supplier_messages.json")
    return data.get("records", [])


def get_supplier_message(message_id: str) -> dict | None:
    for msg in load_supplier_messages():
        if msg.get("message_id") == message_id:
            return msg
    return None


def resolve_contract_text(contract_number: str) -> tuple[str, str]:
    filename = CONTRACT_FILE_BY_NUMBER.get(contract_number)
    if not filename:
        return "", ""
    path = _CONTRACT_DIR / filename
    if not path.exists():
        alt = _ROOT / "data" / "contracts" / filename
        path = alt if alt.exists() else path
    if not path.exists():
        return filename, ""
    return filename, path.read_text(encoding="utf-8")
