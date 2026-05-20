# AGENT_INTAKE.md — Intake Agent Service Specification

> Handles Agents 1 (Requestor Info) and 2 (Vendor Info).
> Port: **8001**
> Calls Groq API with `llama-3.3-70b-versatile`.

---

## Dependencies

```bash
pip install fastapi uvicorn groq pydantic[email]
```

---

## File Structure

```
backend/agents/intake/
├── main.py              # FastAPI app
├── routers/
│   ├── requestor.py     # /agents/intake/requestor
│   └── vendor.py        # /agents/intake/vendor
├── services/
│   └── groq_client.py   # Shared Groq client
├── prompts/
│   ├── requestor.py     # System prompt for requestor agent
│   └── vendor.py        # System prompt for vendor agent
├── requirements.txt
└── Dockerfile
```

---

## Groq Client (shared)

```python
# backend/agents/intake/services/groq_client.py
from groq import Groq
import os, json

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

async def call_groq(system_prompt: str, user_message: str) -> dict:
    """
    Call Groq with a system prompt and user message.
    Forces JSON output. Returns parsed dict.
    """
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.0,
        max_tokens=2048,
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: strip markdown fences if model added them
        clean = raw.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean)
```

---

## Requestor Router

```python
# backend/agents/intake/routers/requestor.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date
from services.groq_client import call_groq
from prompts.requestor import REQUESTOR_SYSTEM_PROMPT
import json

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

{json.dumps(data.dict(), indent=2)}

Return your validation result as JSON.
"""
    try:
        result = await call_groq(REQUESTOR_SYSTEM_PROMPT, user_message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
```

---

## Vendor Router

```python
# backend/agents/intake/routers/vendor.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.groq_client import call_groq
from prompts.vendor import VENDOR_SYSTEM_PROMPT
import json

router = APIRouter()

class VendorInput(BaseModel):
    vendor_name: str
    vendor_address_line1: str
    vendor_address_line2: Optional[str] = None
    vendor_address_county: Optional[str] = None
    vendor_address_state: str
    vendor_address_country: str
    vendor_contact_name: str
    vendor_contact_role: str
    vendor_contact_phone_country_code: str
    vendor_contact_phone: str
    vendor_contact_email: str
    vendor_master_id: Optional[str] = None
    prior_contract_number: Optional[str] = None

@router.post("/agents/intake/vendor")
async def validate_vendor(data: VendorInput):
    user_message = f"""
Validate the following vendor information from a PRS intake form:

{json.dumps(data.dict(), indent=2)}

Return your validation result as JSON.
"""
    try:
        result = await call_groq(VENDOR_SYSTEM_PROMPT, user_message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
```

---

## System Prompts

```python
# backend/agents/intake/prompts/requestor.py
REQUESTOR_SYSTEM_PROMPT = """
You are a healthcare procurement intake validator for a US-based health system.
Your job is to validate the requestor section of a Purchase Request System (PRS) intake form.

Validation rules:
1. All fields must be non-empty strings.
2. business_priority must be exactly one of: "Critical", "High", "Medium", "Low".
3. need_by_date must be a future date in YYYY-MM-DD format.
4. request_description must be at least 10 characters and describe a real procurement need.
5. requestor_name and business_owner must look like real human names (not "N/A", "TBD", "test").
6. Flag any description that appears unrelated to healthcare procurement.
7. If need_by_date is within 7 days, add a warning about expedited review.

Respond ONLY with valid JSON in this exact structure:
{
  "agent": "requestor_info",
  "status": "pass | fail | partial",
  "missing_fields": [],
  "field_errors": [
    { "field": "string", "issue": "string", "value_provided": "string" }
  ],
  "warnings": [],
  "confidence_score": 0.0,
  "summary": "string"
}

No explanation. No markdown. Only the JSON object.
"""
```

```python
# backend/agents/intake/prompts/vendor.py
VENDOR_SYSTEM_PROMPT = """
You are a vendor data quality validator for a US healthcare procurement system.
Your job is to validate vendor information submitted on a PRS intake form.

Validation rules:
1. vendor_name must be a real business name (not placeholder text like "Test", "N/A").
2. vendor_address_line1 is required. Line 2 is optional.
3. vendor_address_state must be a valid 2-letter US state abbreviation (CA, IL, TX, NY, etc.).
4. vendor_address_country should be "US" or a valid ISO 3166-1 alpha-2 code.
5. vendor_contact_phone must be 10 digits for US (+1) or valid international format.
6. vendor_contact_email must be valid email format (user@domain.tld).
7. vendor_contact_phone_country_code must be a valid international dial code (+1, +44, etc.).
8. vendor_master_id and prior_contract_number are OPTIONAL — never flag these as missing.
9. Add a warning if vendor_master_id is absent (new vendor onboarding may be required).

Respond ONLY with valid JSON in this exact structure:
{
  "agent": "vendor_info",
  "status": "pass | fail | partial",
  "missing_fields": [],
  "field_errors": [
    { "field": "string", "issue": "string", "value_provided": "string" }
  ],
  "warnings": [],
  "confidence_score": 0.0,
  "summary": "string"
}

No explanation. No markdown. Only the JSON object.
"""
```

---

## Main App

```python
# backend/agents/intake/main.py
from fastapi import FastAPI
from routers import requestor, vendor

app = FastAPI(title="PRS Intake Agent", version="1.0.0")
app.include_router(requestor.router)
app.include_router(vendor.router)

@app.get("/health")
def health():
    return {"status": "healthy", "service": "intake-agent", "port": 8001}
```

---

## Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

## requirements.txt

```
fastapi==0.111.0
uvicorn==0.29.0
groq==0.9.0
pydantic[email]==2.7.1
```
