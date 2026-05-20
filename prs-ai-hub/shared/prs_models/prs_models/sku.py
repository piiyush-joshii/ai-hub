from pydantic import BaseModel, field_validator


class SKUItem(BaseModel):
    sku_number: str
    description: str
    unit_of_measure: str
    unit_price: float
    msrp: float | None = None
    min_order_qty: int
    lead_time: str
    status: str

    @field_validator("unit_price", "msrp")
    @classmethod
    def must_be_positive(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("Must be a positive number")
        return v


class SKUAddendumRequest(BaseModel):
    request_id: str
    sku_items: list[SKUItem]
    addendum_text: str
