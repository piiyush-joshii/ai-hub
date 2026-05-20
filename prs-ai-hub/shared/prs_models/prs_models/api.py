from typing import Any

from pydantic import BaseModel

from prs_models.intake import RequestorInfo, VendorInfo
from prs_models.sku import SKUItem


class APIResponse(BaseModel):
    success: bool
    request_id: str
    data: Any | None = None
    error: str | None = None


class PRSFullRequest(BaseModel):
    requestor: RequestorInfo
    vendor: VendorInfo
    contract_text: str
    contract_filename: str
    sku_items: list[SKUItem]
    addendum_text: str
