import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()

_DATA_ROOT = Path(os.getenv("DATA_DIR", Path(__file__).resolve().parents[3] / "data"))
FIXTURES_DIR = _DATA_ROOT / "fixtures"


@router.get("")
async def list_fixtures():
    if not FIXTURES_DIR.exists():
        return {"fixtures": []}
    fixtures = []
    for path in sorted(FIXTURES_DIR.glob("*.json")):
        if path.name.endswith(".meta.json"):
            continue
        meta_path = FIXTURES_DIR / f"{path.stem}.meta.json"
        meta = {}
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
        fixtures.append(
            {
                "id": path.stem,
                "label": meta.get("label", path.stem),
                "description": meta.get("description", ""),
                "contract_file": meta.get("contract_file", ""),
                "expected_scenario": meta.get("expected_scenario", ""),
            }
        )
    return {"fixtures": fixtures}


@router.get("/{fixture_id}")
async def get_fixture(fixture_id: str):
    path = FIXTURES_DIR / f"{fixture_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Fixture not found")
    return json.loads(path.read_text())
