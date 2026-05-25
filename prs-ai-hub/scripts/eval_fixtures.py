#!/usr/bin/env python3
"""Phase 0 — replay PRS fixtures and compare overall_status to expected_scenario."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data" / "fixtures"


def main() -> int:
    meta_files = sorted(FIXTURES.glob("*.meta.json"))
    if not meta_files:
        print("No fixtures found. Run: python scripts/generate_fixtures.py")
        return 1

    print("Fixture eval (expected_scenario vs manual review checklist):\n")
    for meta_path in meta_files:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        fid = meta_path.name.replace(".meta.json", "")
        payload_path = FIXTURES / f"{fid}.json"
        sku_count = 0
        if payload_path.exists():
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
            sku_count = len(payload.get("sku_items", []))
        print(f"  {fid}")
        print(f"    expected: {meta.get('expected_scenario')}")
        print(f"    contract: {meta.get('contract_file')}")
        print(f"    skus:     {sku_count}")
        print()

    print(
        "Automated Groq replay is not run here (rate limits). "
        "Submit each fixture in the UI and compare overall_status to expected."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
