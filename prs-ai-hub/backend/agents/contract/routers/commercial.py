from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from prompts.commercial import COMMERCIAL_SYSTEM_PROMPT
from services.groq_client import call_groq, trim_contract

router = APIRouter()


class ContractInput(BaseModel):
    request_id: str
    contract_text: str
    contract_filename: str


@router.post("/agents/contract/commercial")
async def validate_commercial(data: ContractInput):
    text = trim_contract(data.contract_text)
    user_message = f"""
Review the following contract for commercial terms.
Contract file: {data.contract_filename}
Request ID: {data.request_id}

CONTRACT TEXT:
{text}

Return your validation result as JSON.
"""
    try:
        return await call_groq(COMMERCIAL_SYSTEM_PROMPT, user_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}") from e
