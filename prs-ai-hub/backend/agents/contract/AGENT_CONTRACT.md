# AGENT_CONTRACT.md — Contract Validation Agent Service Specification

> Handles Agents 3 (Parties & Definitions), 4 (Commercial Terms), 5 (Legal Clauses).
> Port: **8002**
> All three agents receive the **full contract text** and analyze their respective sections.

---

## Dependencies

```bash
pip install fastapi uvicorn groq pydantic
```

---

## File Structure

```
backend/agents/contract/
├── main.py
├── routers/
│   ├── parties.py        # /agents/contract/parties
│   ├── commercial.py     # /agents/contract/commercial
│   └── legal.py          # /agents/contract/legal
├── services/
│   └── groq_client.py    # Same pattern as intake agent
├── prompts/
│   ├── parties.py
│   ├── commercial.py
│   └── legal.py
├── requirements.txt
└── Dockerfile
```

---

## Shared Input Model

```python
# All three contract endpoints accept this input
class ContractInput(BaseModel):
    request_id: str
    contract_text: str        # Full extracted text from PDF/DOCX
    contract_filename: str
```

---

## Parties & Definitions Prompt

```python
# backend/agents/contract/prompts/parties.py
PARTIES_SYSTEM_PROMPT = """
You are a legal contract analyst for a US healthcare procurement organization.
Review the Parties and Definitions sections of a vendor contract document.

CHECK PARTIES SECTION:
- Both parties are named with full legal names (not just trade names)
- Both parties have a physical address stated
- Entity types are specified for both parties (LLC, Corp, LP, Individual, etc.)
- A "Whereas" / Recitals section exists and establishes business context

CHECK DEFINITIONS SECTION:
- A definitions section exists
- "Services" or equivalent scope term is defined
- "Confidential Information" is defined
- "Term" (contract duration) is defined
- "Agreement" or "Contract" is defined
- "Effective Date" is defined

For healthcare contracts, flag if:
- Either party's entity type is unclear (liability risk)
- Confidential Information definition excludes PHI or HIPAA-related data
- Effective Date is ambiguous

Respond ONLY with this exact JSON structure. No explanation. No markdown.
{
  "agent": "parties_and_definitions",
  "status": "pass | fail | partial",
  "checks": {
    "party_legal_names": "present | partial | missing",
    "party_addresses": "present | partial | missing",
    "entity_types": "present | partial | missing",
    "recitals_whereas": "present | partial | missing",
    "definitions_section": "present | partial | missing",
    "term_services_defined": "present | partial | missing",
    "term_confidential_information_defined": "present | partial | missing",
    "term_term_defined": "present | partial | missing",
    "term_agreement_defined": "present | partial | missing",
    "term_effective_date_defined": "present | partial | missing"
  },
  "issues": [
    { "check": "string", "severity": "high | medium | low", "note": "string" }
  ],
  "confidence_score": 0.0,
  "summary": "string"
}
"""
```

---

## Commercial Terms Prompt

```python
# backend/agents/contract/prompts/commercial.py
COMMERCIAL_SYSTEM_PROMPT = """
You are a commercial contract reviewer for a US healthcare supply chain organization.
Review the commercial terms of a vendor contract.

CHECK SCOPE OF WORK:
- Deliverables are clearly listed and specific
- Timelines or milestones are defined
- Performance standards or SLAs are specified

CHECK PAYMENT TERMS:
- Total amount or pricing structure is stated
- Currency is specified (flag if not USD for US contracts)
- Invoice due dates are defined (Net 30, Net 60, etc.)
- Invoicing instructions or process is described
- Late fees or interest on overdue payments is addressed
- Accepted payment methods are listed (ACH, check, wire, etc.)

CHECK TERM AND TERMINATION:
- Contract start date is explicit
- Contract end date or duration is explicit
- Termination notice period is defined (e.g., 30 days written notice)
- Termination for cause provisions exist
- Termination for convenience provisions exist

FLAG if:
- Payment terms are Net 90+ (unusually long — finance review needed)
- No late fee mentioned (creates collection risk)
- No termination for convenience clause (locks in the contract)
- Auto-renewal language exists (flag for awareness)

Respond ONLY with this exact JSON structure. No explanation. No markdown.
{
  "agent": "commercial_terms",
  "status": "pass | fail | partial",
  "scope_of_work": {
    "deliverables": "present | partial | missing",
    "timelines": "present | partial | missing",
    "performance_standards": "present | partial | missing"
  },
  "payment_terms": {
    "amount_or_pricing": "present | partial | missing",
    "currency": "present | partial | missing",
    "invoice_due_dates": "present | partial | missing",
    "invoicing_process": "present | partial | missing",
    "late_fees": "present | partial | missing",
    "payment_methods": "present | partial | missing"
  },
  "term_and_termination": {
    "start_date": "present | partial | missing",
    "end_date": "present | partial | missing",
    "notice_period": "present | partial | missing",
    "termination_for_cause": "present | partial | missing",
    "termination_for_convenience": "present | partial | missing"
  },
  "risk_flags": [],
  "confidence_score": 0.0,
  "summary": "string"
}
"""
```

---

## Legal Clauses Prompt

```python
# backend/agents/contract/prompts/legal.py
LEGAL_SYSTEM_PROMPT = """
You are a legal compliance reviewer for a US healthcare organization's procurement team.
Verify that a vendor contract contains all required protective legal clauses.

Check each clause and classify as: present, partial, or missing.

REQUIRED CLAUSES:
1. intellectual_property — ownership of work product and IP created under the contract
2. confidentiality_nda — protection of confidential and proprietary information
3. representations_warranties — statements of fact and quality assurances from both parties
4. indemnification — which party indemnifies the other and under what conditions
5. limitation_of_liability — caps on maximum financial exposure for either party
6. dispute_resolution — process for resolving disputes (arbitration, mediation, or litigation)
7. governing_law — which US state's law governs interpretation of the contract
8. force_majeure — excused non-performance under extraordinary circumstances
9. assignment — whether rights/obligations can be transferred to third parties
10. notices — how official written notices must be delivered (email, certified mail, etc.)
11. entire_agreement — this contract supersedes all prior agreements and understandings
12. amendments — how the contract can be formally modified
13. severability — invalid clause does not void the entire contract
14. waiver — failure to enforce a right does not waive future exercise of that right

HIGH RISK FLAGS (for US healthcare):
- Governing law is NOT a US state → jurisdiction ambiguity
- Limitation of liability is missing → uncapped financial exposure
- Confidentiality/NDA is missing → potential HIPAA risk if PHI involved
- Indemnification is entirely one-sided (only one party indemnifies) → unfair risk allocation

MEDIUM RISK FLAGS:
- Force majeure does not address pandemic or regulatory shutdown scenarios
- Assignment clause allows assignment without prior written consent
- Dispute resolution requires out-of-state or international arbitration

Respond ONLY with this exact JSON structure. No explanation. No markdown.
{
  "agent": "legal_clauses",
  "status": "pass | fail | partial",
  "clauses": {
    "intellectual_property": "present | partial | missing",
    "confidentiality_nda": "present | partial | missing",
    "representations_warranties": "present | partial | missing",
    "indemnification": "present | partial | missing",
    "limitation_of_liability": "present | partial | missing",
    "dispute_resolution": "present | partial | missing",
    "governing_law": "present | partial | missing",
    "force_majeure": "present | partial | missing",
    "assignment": "present | partial | missing",
    "notices": "present | partial | missing",
    "entire_agreement": "present | partial | missing",
    "amendments": "present | partial | missing",
    "severability": "present | partial | missing",
    "waiver": "present | partial | missing"
  },
  "missing_clauses": [],
  "high_risk_flags": [],
  "medium_risk_flags": [],
  "confidence_score": 0.0,
  "summary": "string"
}
"""
```

---

## Routers (same pattern for all 3)

```python
# backend/agents/contract/routers/legal.py  (repeat pattern for parties.py, commercial.py)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.groq_client import call_groq
from prompts.legal import LEGAL_SYSTEM_PROMPT

router = APIRouter()

class ContractInput(BaseModel):
    request_id: str
    contract_text: str
    contract_filename: str

@router.post("/agents/contract/legal")
async def validate_legal_clauses(data: ContractInput):
    user_message = f"""
Review the following contract document for required legal clauses.
Contract file: {data.contract_filename}
Request ID: {data.request_id}

CONTRACT TEXT:
{data.contract_text[:15000]}   # Trim to stay within context limits

Return your validation result as JSON.
"""
    try:
        result = await call_groq(LEGAL_SYSTEM_PROMPT, user_message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
```

---

## Main App

```python
# backend/agents/contract/main.py
from fastapi import FastAPI
from routers import parties, commercial, legal

app = FastAPI(title="PRS Contract Agent", version="1.0.0")
app.include_router(parties.router)
app.include_router(commercial.router)
app.include_router(legal.router)

@app.get("/health")
def health():
    return {"status": "healthy", "service": "contract-agent", "port": 8002}
```

---

## Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

## requirements.txt

```
fastapi==0.111.0
uvicorn==0.29.0
groq==0.9.0
pydantic==2.7.1
```
