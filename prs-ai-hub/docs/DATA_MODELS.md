# DATA_MODELS.md — Shared Pydantic Models & JSON Schemas

> All FastAPI services import from a shared `prs_models` package.
> Keep this file as the single source of truth for all data shapes.

---

## Installation

```bash
# Shared models package (used by all 4 services)
pip install -e ./shared/prs_models
```

---

## 1. PRS Intake Models

```python
# shared/prs_models/intake.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import date

class RequestorInfo(BaseModel):
    requestor_name: str
    requestor_business_unit: str
    business_owner: str
    business_unit: str
    business_priority: str          # "Critical" | "High" | "Medium" | "Low"
    request_description: str
    need_by_date: date

    @validator("business_priority")
    def priority_must_be_valid(cls, v):
        allowed = {"Critical", "High", "Medium", "Low"}
        if v not in allowed:
            raise ValueError(f"Must be one of {allowed}")
        return v

class VendorInfo(BaseModel):
    vendor_name: str
    vendor_address_line1: str
    vendor_address_line2: Optional[str] = None
    vendor_address_county: Optional[str] = None
    vendor_address_state: str       # 2-letter US state code
    vendor_address_country: str     # ISO 3166-1 alpha-2
    vendor_contact_name: str
    vendor_contact_role: str
    vendor_contact_phone_country_code: str   # e.g. "+1"
    vendor_contact_phone: str
    vendor_contact_email: EmailStr
    vendor_master_id: Optional[str] = None
    prior_contract_number: Optional[str] = None

class PRSIntakeRequest(BaseModel):
    requestor: RequestorInfo
    vendor: VendorInfo
```

---

## 2. Contract Models

```python
# shared/prs_models/contract.py
from pydantic import BaseModel

class ContractValidationRequest(BaseModel):
    request_id: str
    contract_text: str              # Full extracted text of the contract PDF/DOCX
    contract_filename: str

class ClauseStatus(BaseModel):
    status: str                     # "present" | "partial" | "missing"
    note: Optional[str] = None
```

---

## 3. SKU Models

```python
# shared/prs_models/sku.py
from pydantic import BaseModel, validator
from typing import Optional, List

class SKUItem(BaseModel):
    sku_number: str
    description: str
    unit_of_measure: str            # EA, CS, BX, PK, PR, KG, LB, etc.
    unit_price: float
    msrp: Optional[float] = None
    min_order_qty: int
    lead_time: str                  # e.g. "14 days", "3 weeks"
    status: str                     # "Active" | "Inactive" | "Pending" | "Discontinued"

    @validator("unit_price", "msrp")
    def must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Must be a positive number")
        return v

class SKUAddendumRequest(BaseModel):
    request_id: str
    sku_items: List[SKUItem]
    addendum_text: str              # Full text of the addendum for policy validation
```

---

## 4. Agent Response Models

```python
# shared/prs_models/responses.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class FieldError(BaseModel):
    field: str
    issue: str
    value_provided: Optional[str] = None

class AgentIssue(BaseModel):
    check: str
    severity: str                   # "high" | "medium" | "low"
    note: str

class AgentResponse(BaseModel):
    agent: str
    status: str                     # "pass" | "fail" | "partial"
    confidence_score: float
    summary: str

class RequestorAgentResponse(AgentResponse):
    missing_fields: List[str] = []
    field_errors: List[FieldError] = []
    warnings: List[str] = []

class VendorAgentResponse(AgentResponse):
    missing_fields: List[str] = []
    field_errors: List[FieldError] = []
    warnings: List[str] = []

class ContractClausesResponse(AgentResponse):
    checks: Dict[str, str] = {}     # clause_name -> "present"|"partial"|"missing"
    issues: List[AgentIssue] = []
    high_risk_flags: List[str] = []
    medium_risk_flags: List[str] = []

class SKUItemResult(BaseModel):
    sku_number: str
    status: str
    errors: List[str] = []
    warnings: List[str] = []

class SKUScheduleResponse(AgentResponse):
    total_skus: int
    valid_skus: int
    invalid_skus: int
    sku_results: List[SKUItemResult] = []
```

---

## 5. Orchestrator Final Output

```python
# shared/prs_models/orchestrator.py
from pydantic import BaseModel
from typing import Dict, List, Any
from datetime import datetime

class OrchestratorResult(BaseModel):
    request_id: str
    submitted_at: datetime
    overall_status: str             # "pass" | "fail" | "partial"
    requires_human_review: bool
    agents: Dict[str, str]          # agent_name -> status
    critical_blockers: List[str]
    warnings: List[str]
    next_action: str
    review_time_estimate: str
    agent_results: Dict[str, Any]   # Full agent outputs keyed by agent name
```

---

## 6. API Request/Response Wrappers

```python
# shared/prs_models/api.py
from pydantic import BaseModel
from typing import Any, Optional

class APIResponse(BaseModel):
    success: bool
    request_id: str
    data: Optional[Any] = None
    error: Optional[str] = None

class PRSFullRequest(BaseModel):
    """Single payload sent to gateway — combines all sections"""
    requestor: RequestorInfo
    vendor: VendorInfo
    contract_text: str
    contract_filename: str
    sku_items: List[SKUItem]
    addendum_text: str
```

---

## 7. Database Schema (PostgreSQL)

```sql
-- Run via Alembic migrations

CREATE TABLE prs_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id      VARCHAR(50) UNIQUE NOT NULL,
    submitted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_by    VARCHAR(255),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    payload         JSONB NOT NULL,         -- Full PRSFullRequest
    agent_results   JSONB,                  -- OrchestratorResult
    requires_review BOOLEAN DEFAULT TRUE,
    reviewed_by     VARCHAR(255),
    reviewed_at     TIMESTAMPTZ,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_prs_requests_status ON prs_requests(status);
CREATE INDEX idx_prs_requests_submitted_at ON prs_requests(submitted_at DESC);

CREATE TABLE audit_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id  VARCHAR(50) REFERENCES prs_requests(request_id),
    action      VARCHAR(100) NOT NULL,
    actor       VARCHAR(255),
    details     JSONB,
    timestamp   TIMESTAMPTZ DEFAULT NOW()
);
```
