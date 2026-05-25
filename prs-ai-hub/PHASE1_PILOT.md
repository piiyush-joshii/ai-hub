# Phase 0 + Phase 1 Pilot (implemented)

Pragmatic subset of *AI-First PRS-CCR-Cash Technical v2* on the existing Groq/FastAPI/Next.js stack.

## Phase 0 — Light platform controls

| Capability | API | UI |
|------------|-----|-----|
| Agent run audit log | `GET /api/v1/pilot/runs` | — |
| Approval queue | `GET /api/v1/pilot/approvals` | `/pilot/approvals` |
| Approve / reject | `POST .../approve`, `POST .../reject` | Approvals page |
| Fixture checklist | `python scripts/eval_fixtures.py` | — |

Runs are logged for: PRS 7-agent jobs, batch intake, CCR evaluate, supplier compose.

Approvals are created when:

- PRS `requires_human_review`
- Intake row `fail` / `partial` / not `ready_to_progress`
- CCR `requires_human_approval` or `HARD_EXCEPTION`
- Supplier draft `requires_human_approval`

## Phase 1 — PRS pilot scope

| Doc agent | Implementation |
|-----------|----------------|
| PRS Intake | `POST /agents/intake/vizient` + `/pilot/intake` batch UI |
| Contract Intelligence | Existing 3 contract agents on Submit (unchanged) |
| Supplier Interaction | `:8005` + `/supplier` draft UI |

**Not in this pilot:** SQL Server, Databricks, Agent 365 harness, live email send.

## Services

| Port | Service |
|------|---------|
| 8005 | Supplier Interaction agent |

## Run

```bash
python scripts/sync_enterprise_data.py
./scripts/run_all.sh
```

Open:

- http://localhost:3000/pilot/intake
- http://localhost:3000/supplier
- http://localhost:3000/pilot/approvals

## Deviations from technical v2

Documented intentionally for MVP:

- Postgres/SQLite instead of SQL Server
- JSON sync instead of Databricks reads
- Groq instead of Azure AI Foundry
- Approvals in-app instead of ServiceNow ATC
