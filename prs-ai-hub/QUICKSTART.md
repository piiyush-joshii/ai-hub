# PRS AI Hub — Quick Start

## Prerequisites

- Python 3.11+
- Docker Desktop (for Postgres/Redis, or full stack)
- Groq API key ([console.groq.com](https://console.groq.com))
- Node.js 20+ (for frontend)

---

## Option A — Local Python `.venv` (recommended for development)

### 1. Create venv and install dependencies

```bash
cd prs-ai-hub
chmod +x scripts/*.sh
./scripts/setup_venv.sh
```

### 2. Configure environment

```bash
# Edit .env and set:
#   GROQ_API_KEY=gsk_your_key_here
# Optional fallbacks if the primary model rate-limits or errors:
#   GROQ_FALLBACK_MODELS=openai/gpt-oss-120b,openai/gpt-oss-20b,llama-3.1-8b-instant
```

### 3. Start Postgres + Redis

```bash
./scripts/start_infra.sh
```

### 4. Activate venv and run all backend services

```bash
source .venv/bin/activate
./scripts/run_backend.sh
```

Services:

| Service   | URL                          |
|-----------|------------------------------|
| Gateway   | http://localhost:8000/docs   |
| Intake    | http://localhost:8001/health |
| Contract  | http://localhost:8002/health |
| SKU       | http://localhost:8003/health |
| CCR       | http://localhost:8004/health |
| Supplier  | http://localhost:8005/health |

Sync all enterprise workbooks into JSON (`data/enterprise/*.json` + `manifest.json`):

```bash
python scripts/sync_enterprise_data.py
```

Then:

- **Enterprise** (`/enterprise`) — browse all synced datasets (intake, CCR, cash recon, exceptions, supplier comms, workflows, learning).
- **Intake pilot** (`/pilot/intake`) — batch-validate Vizient intake rows (Phase 1).
- **Supplier** (`/supplier`) — draft supplier emails from message queue (Phase 1).
- **Approvals** (`/pilot/approvals`) — supervised pilot approval queue (Phase 0).
- **CCR** (`/ccr`) — run the CCR agent on transactions from `ccr_decision_input_may2026.xlsx`.

See `PHASE1_PILOT.md` for scope vs the technical v2 document.

### 5. Frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Frontend looks blank (white page)

Usually a **corrupted `.next` cache** (server error `Cannot find module './XXX.js'`). Next also sets `body { display: none }` until load, so a 500 looks like an empty page.

```bash
cd frontend
rm -rf .next
npm run dev
```

If port 3000 is stuck on an old crashed dev server, stop it (`lsof -ti :3000 | xargs kill -9`) or use the URL Next prints (e.g. http://localhost:3001).

---

## Option B — Run with Docker (full stack)

```bash
docker compose up --build
```

| Service        | URL                          |
|----------------|------------------------------|
| Frontend       | http://localhost:3000        |
| API docs       | http://localhost:8000/docs   |
| Intake agent   | http://localhost:8001/health   |

## Local dev (without Docker frontend)

```bash
# Terminal 1 — infrastructure
docker compose up postgres redis intake-agent contract-agent sku-agent gateway

# Terminal 2 — frontend
cd frontend && npm install && npm run dev
```

## Try a sample

1. Open http://localhost:3000/submit
2. Click a **Sample fixture** (e.g. ApexTech Clean)
3. Click **Submit for validation**
4. Watch live agent progress on the results page (~1–2 min for all 7 agents)

## Regenerate fixtures

```bash
python3 scripts/generate_fixtures.py
```
