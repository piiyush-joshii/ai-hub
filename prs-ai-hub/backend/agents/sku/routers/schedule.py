import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from prompts.schedule import SKU_SCHEDULE_SYSTEM_PROMPT
from services.groq_client import call_groq

router = APIRouter()


class SKUItem(BaseModel):
    sku_number: str
    description: str
    unit_of_measure: str
    unit_price: float
    msrp: float | None = None
    min_order_qty: int
    lead_time: str
    status: str


class SKUScheduleInput(BaseModel):
    request_id: str
    sku_items: list[SKUItem]
    addendum_text: str


@router.post("/agents/sku/schedule")
async def validate_sku_schedule(data: SKUScheduleInput):
    user_message = f"""
Validate the following SKU line items from a vendor contract addendum.
Request ID: {data.request_id}

SKU ITEMS:
{json.dumps([item.model_dump() for item in data.sku_items], indent=2)}

Return your validation result as JSON.
"""
    try:
        return await call_groq(SKU_SCHEDULE_SYSTEM_PROMPT, user_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}") from e
