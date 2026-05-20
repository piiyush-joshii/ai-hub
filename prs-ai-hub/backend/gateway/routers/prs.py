import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from services.database import async_session, create_request, delete_request, get_request, list_requests
from services.file_parser import parse_uploaded_file
from services.validation_runner import run_validation_job
from services.ws_manager import ws_manager

router = APIRouter()


class SubmitJSONBody(BaseModel):
    requestor: dict[str, Any]
    vendor: dict[str, Any]
    contract_text: str
    contract_filename: str = "contract.txt"
    sku_items: list[dict[str, Any]] = Field(default_factory=list)
    addendum_text: str = ""


def _new_request_id() -> str:
    return f"PRS-{datetime.now().strftime('%Y')}-{uuid.uuid4().hex[:8].upper()}"


@router.post("/submit")
async def submit_prs(body: SubmitJSONBody):
    request_id = _new_request_id()
    payload = body.model_dump()

    async with async_session() as session:
        await create_request(session, request_id, payload)

    asyncio.create_task(run_validation_job(request_id, payload))

    return {
        "success": True,
        "request_id": request_id,
        "message": "Validation in progress",
        "status_url": f"/api/v1/prs/status/{request_id}",
    }


@router.post("/submit/upload")
async def submit_prs_upload(
    form_data: str = Form(...),
    contract_file: UploadFile = File(...),
    addendum_file: UploadFile | None = File(None),
):
    try:
        data = json.loads(form_data)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid form_data JSON") from e

    contract_bytes = await contract_file.read()
    contract_text = parse_uploaded_file(contract_file.filename or "contract.pdf", contract_bytes)

    addendum_text = data.get("addendum_text", "")
    if addendum_file and addendum_file.filename:
        addendum_bytes = await addendum_file.read()
        addendum_text = parse_uploaded_file(addendum_file.filename, addendum_bytes)

    body = SubmitJSONBody(
        requestor=data["requestor"],
        vendor=data["vendor"],
        contract_text=contract_text,
        contract_filename=contract_file.filename or "contract.txt",
        sku_items=data.get("sku_items", []),
        addendum_text=addendum_text or contract_text[:8000],
    )
    return await submit_prs(body)


@router.post("/parse-document")
async def parse_document(file: UploadFile = File(...)):
    """Extract text from an uploaded contract or addendum (PDF, DOCX, TXT)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    ext = file.filename.lower().split(".")[-1]
    if ext not in ("pdf", "docx", "doc", "txt"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use PDF, DOCX, or TXT.",
        )
    raw = await file.read()
    if len(raw) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 25MB limit")
    try:
        text = parse_uploaded_file(file.filename, raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "filename": file.filename,
        "text": text,
        "char_count": len(text),
    }


@router.get("/status/{request_id}")
async def get_status(request_id: str):
    async with async_session() as session:
        row = await get_request(session, request_id)
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")
    return {
        "request_id": row.request_id,
        "status": row.status,
        "submitted_at": row.submitted_at.isoformat(),
        "result": row.agent_results,
        "error": row.error,
    }


@router.get("/history")
async def get_history(page: int = 1, limit: int = 20, status: str | None = None):
    async with async_session() as session:
        rows, total = await list_requests(session, page=page, limit=limit, status=status)

    items = []
    for row in rows:
        vendor_name = (row.payload or {}).get("vendor", {}).get("vendor_name", "—")
        items.append(
            {
                "request_id": row.request_id,
                "submitted_at": row.submitted_at.isoformat(),
                "status": row.status,
                "overall_status": (row.agent_results or {}).get("overall_status"),
                "vendor_name": vendor_name,
                "requires_review": row.requires_review,
            }
        )
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.delete("/{request_id}")
async def delete_prs_request(request_id: str):
    async with async_session() as session:
        deleted = await delete_request(session, request_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"success": True, "request_id": request_id}


@router.get("/{request_id}")
async def get_request_detail(request_id: str):
    async with async_session() as session:
        row = await get_request(session, request_id)
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")
    return {
        "request_id": row.request_id,
        "status": row.status,
        "submitted_at": row.submitted_at.isoformat(),
        "payload": row.payload,
        "result": row.agent_results,
        "error": row.error,
    }


@router.websocket("/ws/{request_id}")
async def prs_websocket(websocket: WebSocket, request_id: str):
    await ws_manager.connect(request_id, websocket)
    try:
        async with async_session() as session:
            row = await get_request(session, request_id)
        if row and row.status == "complete" and row.agent_results:
            await websocket.send_json(
                {
                    "event": "validation_complete",
                    "overall_status": row.agent_results.get("overall_status"),
                    "result": row.agent_results,
                }
            )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(request_id, websocket)
