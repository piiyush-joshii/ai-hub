import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from prompts.compose import SUPPLIER_COMPOSE_SYSTEM_PROMPT
from services.groq_client import call_groq

router = APIRouter()


class ComposeInput(BaseModel):
    message: dict = Field(description="Row from supplier_messages.json")
    template_hint: str = ""


@router.post("/agents/supplier/compose")
async def compose_supplier_message(data: ComposeInput):
    user_message = f"""
Draft supplier communication for human approval before send.

MESSAGE QUEUE RECORD:
{json.dumps(data.message, indent=2)}

TEMPLATE HINT: {data.template_hint or "Use standard professional healthcare procurement tone."}

Return JSON only.
"""
    try:
        return await call_groq(SUPPLIER_COMPOSE_SYSTEM_PROMPT, user_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}") from e
