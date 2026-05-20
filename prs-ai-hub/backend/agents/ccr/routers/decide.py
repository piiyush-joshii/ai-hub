from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from prompts.ccr import CCR_DECISION_SYSTEM_PROMPT
from services.groq_client import call_groq

router = APIRouter()

MAX_CONTRACT_CHARS = 12000


class CCRDecisionInput(BaseModel):
    transaction_id: str
    transaction: dict
    contract_text: str = ""
    contract_filename: str = ""


def _trim_contract(text: str) -> str:
    if len(text) <= MAX_CONTRACT_CHARS:
        return text
    return text[:MAX_CONTRACT_CHARS] + "\n\n[... truncated ...]"


@router.post("/agents/ccr/decide")
async def decide_ccr(data: CCRDecisionInput):
    txn = data.transaction
    contract_excerpt = _trim_contract(data.contract_text or "")

    user_message = f"""
Evaluate this invoice transaction for CCR decision.

TRANSACTION (PRS + runtime context):
{txn}

CONTRACT DOCUMENT ({data.contract_filename or 'n/a'}):
{contract_excerpt or '[No contract text available — decide using transaction contract_status fields only]'}

Return JSON only.
"""
    try:
        return await call_groq(CCR_DECISION_SYSTEM_PROMPT, user_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}") from e
