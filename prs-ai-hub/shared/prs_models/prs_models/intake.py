from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, field_validator

Priority = Literal["Critical", "High", "Medium", "Low"]


class RequestorInfo(BaseModel):
    requestor_name: str
    requestor_business_unit: str
    business_owner: str
    business_unit: str
    business_priority: str
    request_description: str
    need_by_date: date

    @field_validator("business_priority")
    @classmethod
    def priority_must_be_valid(cls, v: str) -> str:
        allowed = {"Critical", "High", "Medium", "Low"}
        if v not in allowed:
            raise ValueError(f"Must be one of {allowed}")
        return v


class VendorInfo(BaseModel):
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
    vendor_contact_email: EmailStr
    vendor_master_id: str | None = None
    prior_contract_number: str | None = None


class PRSIntakeRequest(BaseModel):
    requestor: RequestorInfo
    vendor: VendorInfo
