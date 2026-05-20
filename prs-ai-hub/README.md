# PRS AI Hub — Purchase Request & Contract Validation System

> **Healthcare-grade** multi-agent AI system for automating purchase request intake and contract validation. Built for the US market with HIPAA-aware design principles.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────┐
│           React / Next.js Frontend           │
│     (Healthcare UI — WCAG 2.1 AA compliant) │
└────────────────────┬────────────────────────┘
                     │ REST + WebSocket
┌────────────────────▼────────────────────────┐
│         FastAPI Gateway  (:8000)             │
│     Auth · Routing · Request Tracking        │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│        LangGraph Orchestrator                │
│   State machine · Parallel fan-out · Merge   │
└──────┬─────────────┬──────────────┬─────────┘
       │             │              │
┌──────▼───┐  ┌──────▼───┐  ┌──────▼───┐
│  Intake   │  │ Contract  │  │   SKU    │
│  Agent    │  │  Agent    │  │  Agent   │
│  :8001    │  │  :8002    │  │  :8003   │
└──────┬───┘  └──────┬───┘  └──────┬───┘
       └─────────────▼──────────────┘
              ┌──────────────┐
              │   Groq API   │
              │ llama-3.3-70b│
              └──────────────┘
┌─────────────┬──────────────┬──────────────┐
│ PostgreSQL  │    Redis     │  LangSmith   │
└─────────────┴──────────────┴──────────────┘
```

---

## 📁 Project Structure

```
prs-ai-hub/
├── frontend/                  # Next.js 14 app
│   ├── FRONTEND.md
├── backend/
│   ├── gateway/               # FastAPI gateway :8000
│   │   └── GATEWAY.md
│   └── agents/
│       ├── intake/            # Intake agent :8001
│       │   └── AGENT_INTAKE.md
│       ├── contract/          # Contract agent :8002
│       │   └── AGENT_CONTRACT.md
│       └── sku/               # SKU agent :8003
│           └── AGENT_SKU.md
├── orchestrator/
│   └── ORCHESTRATOR.md
├── docs/
│   ├── AGENTS.md
│   ├── DATA_MODELS.md
│   ├── ENV.md
│   └── DEPLOYMENT.md
└── README.md
```

---

## ⚡ Quick Start

```bash
# 1. Clone & set up env
cp .env.example .env
# Fill in GROQ_API_KEY (see docs/ENV.md)

# 2. Start all services
docker-compose up --build

# 3. Frontend
cd frontend && npm install && npm run dev
# → http://localhost:3000

# 4. API docs
# → http://localhost:8000/docs
```

---

## 🤖 Agent Overview

| Agent | Port | Responsibility | Model |
|-------|------|----------------|-------|
| Intake Agent | 8001 | Validates PRS form fields & vendor info | llama-3.3-70b-versatile |
| Contract Agent | 8002 | Validates 20+ contract clauses | llama-3.3-70b-versatile |
| SKU Agent | 8003 | Validates SKU schedule & pricing policies | llama-3.3-70b-versatile |

---

## 🏥 Healthcare Compliance Notes

- WCAG 2.1 AA compliant UI
- No PHI stored in LLM prompts — contract metadata only
- Full audit trail on all API responses
- RBAC on all routes
- TLS enforced in production

---

## 📚 Read Next

1. `docs/AGENTS.md` — Agent prompts, output schemas, business rules
2. `docs/DATA_MODELS.md` — Shared Pydantic models
3. `frontend/FRONTEND.md` — UI spec and design system
4. `orchestrator/ORCHESTRATOR.md` — LangGraph graph definition
5. `docs/ENV.md` — Environment variables
6. `docs/DEPLOYMENT.md` — Docker & production deployment
