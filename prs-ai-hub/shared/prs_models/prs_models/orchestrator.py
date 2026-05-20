from datetime import datetime
from typing import Any

from pydantic import BaseModel


class OrchestratorResult(BaseModel):
    request_id: str
    submitted_at: datetime
    overall_status: str
    requires_human_review: bool
    agents: dict[str, str]
    critical_blockers: list[str]
    warnings: list[str]
    next_action: str
    review_time_estimate: str
    agent_results: dict[str, Any]
