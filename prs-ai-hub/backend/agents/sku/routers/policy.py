from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from prompts.policy import SKU_POLICY_SYSTEM_PROMPT
from services.groq_client import call_groq

router = APIRouter()
MAX_ADDENDUM_CHARS = 12000


class SKUPolicyInput(BaseModel):
    request_id: str
    addendum_text: str


@router.post("/agents/sku/policy")
async def validate_sku_policy(data: SKUPolicyInput):
    text = data.addendum_text[:MAX_ADDENDUM_CHARS]
    user_message = f"""
Review the following SKU addendum document for required policy sections.
Request ID: {data.request_id}

ADDENDUM TEXT:
{text}

Return your validation result as JSON.
"""
    try:
        return await call_groq(SKU_POLICY_SYSTEM_PROMPT, user_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}") from e
