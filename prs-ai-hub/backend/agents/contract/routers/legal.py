from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from prompts.legal import LEGAL_SYSTEM_PROMPT
from services.groq_client import call_groq, trim_contract

router = APIRouter()


class ContractInput(BaseModel):
    request_id: str
    contract_text: str
    contract_filename: str


@router.post("/agents/contract/legal")
async def validate_legal(data: ContractInput):
    text = trim_contract(data.contract_text)
    user_message = f"""
Review the following contract for required legal clauses.
Contract file: {data.contract_filename}
Request ID: {data.request_id}

CONTRACT TEXT:
{text}

Return your validation result as JSON.
"""
    try:
        return await call_groq(LEGAL_SYSTEM_PROMPT, user_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}") from e
