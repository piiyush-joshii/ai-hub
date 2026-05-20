import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from prompts.requestor import REQUESTOR_SYSTEM_PROMPT
from services.groq_client import call_groq

router = APIRouter()


class RequestorInput(BaseModel):
    requestor_name: str
    requestor_business_unit: str
    business_owner: str
    business_unit: str
    business_priority: str
    request_description: str
    need_by_date: str


@router.post("/agents/intake/requestor")
async def validate_requestor(data: RequestorInput):
    user_message = f"""
Validate the following requestor information from a PRS intake form:

{json.dumps(data.model_dump(), indent=2)}

Return your validation result as JSON.
"""
    try:
        return await call_groq(REQUESTOR_SYSTEM_PROMPT, user_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}") from e
