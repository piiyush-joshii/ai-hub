import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from prompts.vizient import VIZIENT_INTAKE_SYSTEM_PROMPT
from services.groq_client import call_groq

router = APIRouter()


class VizientSubmissionInput(BaseModel):
    submission: dict = Field(description="Full row from intake_submissions.json")
    validation_rules: list[dict] = Field(default_factory=list)


@router.post("/agents/intake/vizient")
async def validate_vizient_submission(data: VizientSubmissionInput):
    sub = data.submission
    key = f"{sub.get('supplier_id', '')}:{sub.get('invoice_number', '')}"
    user_message = f"""
Validate this Vizient intake submission row.

Submission key: {key}

SUBMISSION ROW:
{json.dumps(sub, indent=2)}

REFERENCE RULES (field catalog):
{json.dumps(data.validation_rules[:12], indent=2) if data.validation_rules else "[]"}

Return JSON only.
"""
    try:
        result = await call_groq(VIZIENT_INTAKE_SYSTEM_PROMPT, user_message)
        result.setdefault("submission_key", key)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}") from e
