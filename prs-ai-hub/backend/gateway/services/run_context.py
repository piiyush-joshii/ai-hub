"""Phase 0 — shared run ID for a validation or pilot job."""
import uuid
from contextvars import ContextVar

_current_run_id: ContextVar[str | None] = ContextVar("current_run_id", default=None)


def new_run_id() -> str:
    rid = f"RUN-{uuid.uuid4().hex[:12].upper()}"
    _current_run_id.set(rid)
    return rid


def get_run_id() -> str | None:
    return _current_run_id.get()
