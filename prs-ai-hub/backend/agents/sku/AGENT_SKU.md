# AGENT_SKU.md — SKU Addendum Agent Service Specification

> Handles Agents 6 (SKU Schedule) and 7 (SKU Policy).
> Port: **8003**

---

## File Structure

```
backend/agents/sku/
├── main.py
├── routers/
│   ├── schedule.py       # /agents/sku/schedule
│   └── policy.py         # /agents/sku/policy
├── services/
│   └── groq_client.py
├── prompts/
│   ├── schedule.py
│   └── policy.py
├── requirements.txt
└── Dockerfile
```

---

## SKU Schedule Prompt

```python
# backend/agents/sku/prompts/schedule.py
SKU_SCHEDULE_SYSTEM_PROMPT = """
You are a procurement data validator for a US healthcare supply chain system.
Validate each SKU line item in the vendor contract addendum.

For EACH SKU item, check:
1. sku_number — must be present and non-empty
2. description — must be meaningful (not "N/A", "TBD", "test", or empty)
3. unit_of_measure — must be a standard abbreviation: EA, CS, BX, PK, PR, KG, LB, DZ, GL, OZ
4. unit_price — must be a positive number greater than 0
5. msrp — if provided, must be >= unit_price (pricing error if unit_price > msrp)
6. min_order_qty — must be a positive integer
7. lead_time — must be specified in days or weeks (e.g., "14 days", "3 weeks")
8. status — must be one of: Active, Inactive, Pending, Discontinued

FLAG as error:
- unit_price > msrp (pricing inconsistency)
- status = "Discontinued" on an active addendum (should not be listed)

FLAG as warning:
- lead_time > 90 days (supply chain risk for healthcare)
- msrp is absent (missing for comparison)
- min_order_qty > 1000 (unusually high — verify)

Respond ONLY with this exact JSON structure. No explanation. No markdown.
{
  "agent": "sku_schedule",
  "status": "pass | fail | partial",
  "total_skus": 0,
  "valid_skus": 0,
  "invalid_skus": 0,
  "sku_results": [
    {
      "sku_number": "string",
      "status": "pass | fail | partial",
      "errors": [],
      "warnings": []
    }
  ],
  "confidence_score": 0.0,
  "summary": "string"
}
"""
```

---

## SKU Policy Prompt

```python
# backend/agents/sku/prompts/policy.py
SKU_POLICY_SYSTEM_PROMPT = """
You are a procurement policy compliance reviewer for a US healthcare organization.
Review the policy sections of a vendor SKU addendum document.

CHECK PRICING POLICIES:
- price_change_notice: Is there a requirement for advance notice before price changes? (e.g., 30 days)
- price_protection_period: Is there a price freeze or protection period defined?
- volume_discounts: Are volume discount tiers or rebate structures described?

CHECK MINIMUM PURCHASE COMMITMENTS:
- minimum_amounts_defined: Are annual or periodic minimum purchase amounts specified?
- consequences_for_shortfall: What happens if minimums are not met? Is this specified?
- measurement_period: Is the measurement period clearly defined (quarterly, annually)?

CHECK PRODUCT CHANGE POLICIES:
- new_sku_process: Is there a process for adding new SKUs to the addendum?
- substitution_policy: Is there a product substitution or equivalent policy?
- discontinuation_notice: Is there a required notice period before discontinuing a product?
- regulatory_accommodation: Does the policy address FDA or regulatory-driven changes?

CHECK REGULATORY & SAFETY:
- compliance_representations: Does vendor represent products comply with applicable regulations (FDA, UL, etc.)?
- safety_escalation_process: Is there a defined process for reporting product safety concerns?
- recall_procedures: Are product recall procedures defined? (CRITICAL for healthcare)

CHECK GENERAL PROVISIONS:
- representations: Vendor representations about product quality and accuracy of specifications
- audit_rights: Does the customer have rights to audit pricing or vendor compliance?

HIGH RISK FLAGS (healthcare-specific):
- recall_procedures missing → critical patient safety gap
- safety_escalation_process missing → regulatory risk
- compliance_representations missing → unknown product compliance status

MEDIUM RISK FLAGS:
- price_change_notice missing → prices can change without warning
- minimum_amounts but no consequences_for_shortfall → unenforceable commitment
- discontinuation_notice missing → products can be cut without notice

Respond ONLY with this exact JSON structure. No explanation. No markdown.
{
  "agent": "sku_policy",
  "status": "pass | fail | partial",
  "pricing_policies": {
    "price_change_notice": "present | partial | missing",
    "price_protection_period": "present | partial | missing",
    "volume_discounts": "present | partial | missing"
  },
  "purchase_commitments": {
    "minimum_amounts_defined": "present | partial | missing",
    "consequences_for_shortfall": "present | partial | missing",
    "measurement_period": "present | partial | missing"
  },
  "product_change_policies": {
    "new_sku_process": "present | partial | missing",
    "substitution_policy": "present | partial | missing",
    "discontinuation_notice": "present | partial | missing",
    "regulatory_accommodation": "present | partial | missing"
  },
  "regulatory_safety": {
    "compliance_representations": "present | partial | missing",
    "safety_escalation_process": "present | partial | missing",
    "recall_procedures": "present | partial | missing"
  },
  "high_risk_flags": [],
  "medium_risk_flags": [],
  "confidence_score": 0.0,
  "summary": "string"
}
"""
```

---

## SKU Schedule Router

```python
# backend/agents/sku/routers/schedule.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.groq_client import call_groq
from prompts.schedule import SKU_SCHEDULE_SYSTEM_PROMPT
import json

router = APIRouter()

class SKUItem(BaseModel):
    sku_number: str
    description: str
    unit_of_measure: str
    unit_price: float
    msrp: Optional[float] = None
    min_order_qty: int
    lead_time: str
    status: str

class SKUScheduleInput(BaseModel):
    request_id: str
    sku_items: List[SKUItem]
    addendum_text: str

@router.post("/agents/sku/schedule")
async def validate_sku_schedule(data: SKUScheduleInput):
    user_message = f"""
Validate the following SKU line items from a vendor contract addendum.
Request ID: {data.request_id}

SKU ITEMS:
{json.dumps([item.dict() for item in data.sku_items], indent=2)}

Return your validation result as JSON.
"""
    try:
        result = await call_groq(SKU_SCHEDULE_SYSTEM_PROMPT, user_message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
```

---

## SKU Policy Router

```python
# backend/agents/sku/routers/policy.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.groq_client import call_groq
from prompts.policy import SKU_POLICY_SYSTEM_PROMPT

router = APIRouter()

class SKUPolicyInput(BaseModel):
    request_id: str
    addendum_text: str

@router.post("/agents/sku/policy")
async def validate_sku_policy(data: SKUPolicyInput):
    user_message = f"""
Review the following SKU addendum document for required policy sections.
Request ID: {data.request_id}

ADDENDUM TEXT:
{data.addendum_text[:12000]}

Return your validation result as JSON.
"""
    try:
        result = await call_groq(SKU_POLICY_SYSTEM_PROMPT, user_message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
```

---

## Main App

```python
# backend/agents/sku/main.py
from fastapi import FastAPI
from routers import schedule, policy

app = FastAPI(title="PRS SKU Agent", version="1.0.0")
app.include_router(schedule.router)
app.include_router(policy.router)

@app.get("/health")
def health():
    return {"status": "healthy", "service": "sku-agent", "port": 8003}
```

---

## Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
```

## requirements.txt

```
fastapi==0.111.0
uvicorn==0.29.0
groq==0.9.0
pydantic==2.7.1
```
