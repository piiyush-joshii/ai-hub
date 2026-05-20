from fastapi import APIRouter, HTTPException

from services.enterprise_data import load_dataset, load_manifest

router = APIRouter()


@router.get("/manifest")
async def enterprise_manifest():
    manifest = load_manifest()
    if not manifest:
        raise HTTPException(
            status_code=404,
            detail="Enterprise data not synced. Run: python scripts/sync_enterprise_data.py",
        )
    return manifest


@router.get("/datasets/{dataset_id}")
async def get_enterprise_dataset(dataset_id: str):
    data = load_dataset(dataset_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Unknown or missing dataset: {dataset_id}")
    records = data.get("records") or data.get("transactions") or []
    return {
        "dataset_id": dataset_id,
        "source": data.get("source"),
        "records": records,
        "total": len(records),
    }
