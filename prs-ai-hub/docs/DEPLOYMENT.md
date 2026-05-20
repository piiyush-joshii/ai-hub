# DEPLOYMENT.md — Docker & Production Deployment

---

## docker-compose.yml (Development)

```yaml
version: "3.9"

services:

  # ── Frontend ────────────────────────────────────────────────
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
    depends_on:
      - gateway

  # ── Gateway ─────────────────────────────────────────────────
  gateway:
    build: ./backend/gateway
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      - INTAKE_AGENT_URL=http://intake-agent:8001
      - CONTRACT_AGENT_URL=http://contract-agent:8002
      - SKU_AGENT_URL=http://sku-agent:8003
      - DATABASE_URL=postgresql+asyncpg://prs_user:prs_password@postgres:5432/prs_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
      - intake-agent
      - contract-agent
      - sku-agent

  # ── Intake Agent ─────────────────────────────────────────────
  intake-agent:
    build: ./backend/agents/intake
    ports:
      - "8001:8001"
    env_file: .env

  # ── Contract Agent ───────────────────────────────────────────
  contract-agent:
    build: ./backend/agents/contract
    ports:
      - "8002:8002"
    env_file: .env

  # ── SKU Agent ────────────────────────────────────────────────
  sku-agent:
    build: ./backend/agents/sku
    ports:
      - "8003:8003"
    env_file: .env

  # ── PostgreSQL ───────────────────────────────────────────────
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: prs_db
      POSTGRES_USER: prs_user
      POSTGRES_PASSWORD: prs_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # ── Redis ────────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## Production Checklist

### Security
- [ ] `JWT_SECRET_KEY` set to cryptographically random 64-char string
- [ ] `GROQ_API_KEY` stored in AWS Secrets Manager / Vault (not `.env`)
- [ ] TLS certificates configured (use AWS ACM or Let's Encrypt)
- [ ] All inter-service traffic on private VPC subnet
- [ ] Database password is strong and rotated
- [ ] CORS origins restricted to production frontend domain only
- [ ] Rate limiting enabled on gateway (100 req/min per IP)

### Scaling
- [ ] Gateway: 2-4 instances behind ALB
- [ ] Agent services: 2 instances each (stateless, scale independently)
- [ ] PostgreSQL: RDS Multi-AZ (us-east-1 for US healthcare)
- [ ] Redis: ElastiCache cluster mode

### Monitoring
- [ ] LangSmith tracing enabled (`LANGCHAIN_TRACING_V2=true`)
- [ ] CloudWatch alerts for:
  - Agent error rate > 5%
  - P99 latency > 30 seconds
  - Database connection pool exhaustion
- [ ] Health check endpoints monitored: `/health` on all services

### Compliance (US Healthcare)
- [ ] All data at rest encrypted (RDS encryption + EBS encryption)
- [ ] All data in transit encrypted (TLS 1.2+)
- [ ] VPC with private subnets for all backend services
- [ ] CloudTrail enabled for API audit logging
- [ ] No PHI sent to Groq API (contract metadata only — verify with legal)
- [ ] BAA with Groq if any PHI will be processed

---

## Running Locally (without Docker)

```bash
# Terminal 1 — PostgreSQL & Redis
docker-compose up postgres redis

# Terminal 2 — Intake Agent
cd backend/agents/intake
uvicorn main:app --port 8001 --reload

# Terminal 3 — Contract Agent
cd backend/agents/contract
uvicorn main:app --port 8002 --reload

# Terminal 4 — SKU Agent
cd backend/agents/sku
uvicorn main:app --port 8003 --reload

# Terminal 5 — Gateway
cd backend/gateway
uvicorn main:app --port 8000 --reload

# Terminal 6 — Frontend
cd frontend
npm run dev
```

---

## Database Migrations

```bash
# From backend/gateway/
alembic init alembic
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```
