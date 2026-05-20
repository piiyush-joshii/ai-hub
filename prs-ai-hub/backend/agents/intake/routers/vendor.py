import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from prompts.vendor import VENDOR_SYSTEM_PROMPT
from services.groq_client import call_groq

router = APIRouter()


class VendorInput(BaseModel):
    vendor_name: str
    vendor_address_line1: str
    vendor_address_line2: str | None = None
    vendor_address_county: str | None = None
    vendor_address_state: str
    vendor_address_country: str
    vendor_contact_name: str
    vendor_contact_role: str
    vendor_contact_phone_country_code: str
    vendor_contact_phone: str
    vendor_contact_email: str
    vendor_master_id: str | None = None
    prior_contract_number: str | None = None


@router.post("/agents/intake/vendor")
async def validate_vendor(data: VendorInput):
    user_message = f"""
Validate the following vendor information from a PRS intake form:

{json.dumps(data.model_dump(), indent=2)}

Return your validation result as JSON.
"""
    try:
        return await call_groq(VENDOR_SYSTEM_PROMPT, user_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}") from e
