import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import JSON, Boolean, DateTime, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DB_PATH = (_ROOT / "data" / "prs_local.db").resolve()


def _resolve_database_url(url: str) -> str:
    prefix = "sqlite+aiosqlite:///"
    if url.startswith(prefix):
        db_path = url[len(prefix) :]
        if not db_path.startswith("/"):
            db_path = str((_ROOT / db_path).resolve())
        db_path = str(Path(db_path).resolve())
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return f"{prefix}{db_path}"
    return url


DATABASE_URL = _resolve_database_url(
    os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH}")
)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_async_engine(DATABASE_URL, echo=False, connect_args=_connect_args)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class PRSRequest(Base):
    __tablename__ = "prs_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    payload: Mapped[dict] = mapped_column(JSON)
    agent_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    requires_review: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class AgentRunLog(Base):
    """Phase 0 — per-agent execution audit trail."""

    __tablename__ = "agent_run_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    parent_ref: Mapped[str] = mapped_column(String(80), index=True)
    agent_name: Mapped[str] = mapped_column(String(64))
    phase: Mapped[str] = mapped_column(String(32), default="prs")
    status: Mapped[str] = mapped_column(String(20))
    model_used: Mapped[str | None] = mapped_column(String(80), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(nullable=True)
    output_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ApprovalItem(Base):
    """Phase 0 — human approval queue for supervised pilot."""

    __tablename__ = "approval_queue"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_type: Mapped[str] = mapped_column(String(40), index=True)
    ref_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    agent_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_request(session: AsyncSession, request_id: str, payload: dict) -> PRSRequest:
    row = PRSRequest(
        request_id=request_id,
        submitted_at=datetime.now(timezone.utc),
        status="pending",
        payload=payload,
        requires_review=True,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def update_request_status(
    session: AsyncSession,
    request_id: str,
    status: str,
    agent_results: dict | None = None,
    error: str | None = None,
) -> None:
    result = await session.execute(select(PRSRequest).where(PRSRequest.request_id == request_id))
    row = result.scalar_one_or_none()
    if not row:
        return
    row.status = status
    if agent_results is not None:
        row.agent_results = agent_results
        row.requires_review = agent_results.get("requires_human_review", True)
    if error is not None:
        row.error = error
    await session.commit()


async def get_request(session: AsyncSession, request_id: str) -> PRSRequest | None:
    result = await session.execute(select(PRSRequest).where(PRSRequest.request_id == request_id))
    return result.scalar_one_or_none()


async def delete_request(session: AsyncSession, request_id: str) -> bool:
    result = await session.execute(select(PRSRequest).where(PRSRequest.request_id == request_id))
    row = result.scalar_one_or_none()
    if not row:
        return False
    await session.delete(row)
    await session.commit()
    return True


async def list_requests(
    session: AsyncSession, page: int = 1, limit: int = 20, status: str | None = None
) -> tuple[list[PRSRequest], int]:
    query = select(PRSRequest).order_by(PRSRequest.submitted_at.desc())
    if status:
        query = query.where(PRSRequest.status == status)
    result = await session.execute(query)
    rows = list(result.scalars().all())
    total = len(rows)
    start = (page - 1) * limit
    return rows[start : start + limit], total


async def log_agent_run(
    session: AsyncSession,
    *,
    run_id: str,
    parent_ref: str,
    agent_name: str,
    phase: str,
    status: str,
    result: dict | None = None,
    output_status: str | None = None,
    model_used: str | None = None,
    latency_ms: int | None = None,
    error: str | None = None,
) -> AgentRunLog:
    row = AgentRunLog(
        run_id=run_id,
        parent_ref=parent_ref,
        agent_name=agent_name,
        phase=phase,
        status=status,
        result=result,
        output_status=output_status,
        model_used=model_used,
        latency_ms=latency_ms,
        error=error,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def list_run_logs(
    session: AsyncSession, parent_ref: str | None = None, limit: int = 100
) -> list[AgentRunLog]:
    query = select(AgentRunLog).order_by(AgentRunLog.created_at.desc()).limit(limit)
    if parent_ref:
        query = query.where(AgentRunLog.parent_ref == parent_ref)
    result = await session.execute(query)
    return list(result.scalars().all())


async def create_approval(
    session: AsyncSession,
    *,
    item_type: str,
    ref_id: str,
    title: str,
    payload: dict,
    agent_result: dict | None = None,
) -> ApprovalItem:
    existing = await session.execute(select(ApprovalItem).where(ApprovalItem.ref_id == ref_id))
    found = existing.scalar_one_or_none()
    if found:
        return found
    row = ApprovalItem(
        item_type=item_type,
        ref_id=ref_id,
        title=title,
        payload=payload,
        agent_result=agent_result,
        status="pending",
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def list_approvals(
    session: AsyncSession, status: str | None = "pending", limit: int = 50
) -> list[ApprovalItem]:
    query = select(ApprovalItem).order_by(ApprovalItem.created_at.desc()).limit(limit)
    if status:
        query = query.where(ApprovalItem.status == status)
    result = await session.execute(query)
    return list(result.scalars().all())


async def decide_approval(
    session: AsyncSession,
    ref_id: str,
    decision: str,
    decided_by: str = "operator",
    note: str | None = None,
) -> ApprovalItem | None:
    result = await session.execute(select(ApprovalItem).where(ApprovalItem.ref_id == ref_id))
    row = result.scalar_one_or_none()
    if not row:
        return None
    row.status = decision
    row.decided_at = datetime.now(timezone.utc)
    row.decided_by = decided_by
    row.note = note
    await session.commit()
    await session.refresh(row)
    return row
