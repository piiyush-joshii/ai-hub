# ENV.md — Environment Variables Guide

> Copy `.env.example` to `.env` and fill in all required values before running any service.

---

## .env.example

```bash
# ============================================================
# GROQ API — Primary LLM Provider
# ============================================================
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1

# ============================================================
# DATABASE — PostgreSQL
# ============================================================
DATABASE_URL=postgresql+asyncpg://prs_user:prs_password@localhost:5432/prs_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=prs_db
DB_USER=prs_user
DB_PASSWORD=prs_password

# ============================================================
# REDIS — Job Queue & Caching
# ============================================================
REDIS_URL=redis://localhost:6379/0

# ============================================================
# SERVICE PORTS
# ============================================================
GATEWAY_PORT=8000
INTAKE_AGENT_PORT=8001
CONTRACT_AGENT_PORT=8002
SKU_AGENT_PORT=8003

# ============================================================
# INTER-SERVICE URLs (used by orchestrator & gateway)
# ============================================================
INTAKE_AGENT_URL=http://localhost:8001
CONTRACT_AGENT_URL=http://localhost:8002
SKU_AGENT_URL=http://localhost:8003

# ============================================================
# AUTH & SECURITY
# ============================================================
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-prod
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480     # 8 hours for healthcare shift workers
API_KEY_HEADER=X-PRS-API-Key

# ============================================================
# LANGSMITH — Observability & Tracing (optional but recommended)
# ============================================================
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=prs-ai-hub
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# ============================================================
# FRONTEND
# ============================================================
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=PRS AI Hub
NEXT_PUBLIC_ENVIRONMENT=development

# ============================================================
# LOGGING
# ============================================================
LOG_LEVEL=INFO          # DEBUG | INFO | WARNING | ERROR
LOG_FORMAT=json         # json | text

# ============================================================
# CORS (comma-separated allowed origins)
# ============================================================
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# ============================================================
# FILE UPLOAD
# ============================================================
MAX_UPLOAD_SIZE_MB=25
ALLOWED_FILE_TYPES=pdf,docx,doc
```

---

## Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ Yes | — | Your Groq API key from console.groq.com |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model to use |
| `DATABASE_URL` | ✅ Yes | — | Full async PostgreSQL connection string |
| `REDIS_URL` | ✅ Yes | — | Redis connection string |
| `JWT_SECRET_KEY` | ✅ Yes | — | Change this before deploying to production |
| `LANGCHAIN_API_KEY` | No | — | LangSmith key for tracing (recommended) |

---

## Getting Your Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up / log in
3. Navigate to **API Keys** → **Create API Key**
4. Copy the key and paste it as `GROQ_API_KEY` in your `.env`

> Groq offers very fast inference (low latency) which is important for a good UX
> when all 7 agents run in parallel.

---

## Production Secrets Management

**Never commit `.env` to git.**

For production, use one of:
- **AWS Secrets Manager** — recommended for US healthcare (HIPAA eligible)
- **HashiCorp Vault**
- **Azure Key Vault**
- **GCP Secret Manager**

Example with AWS Secrets Manager:
```python
import boto3, json

def get_secret(secret_name: str) -> dict:
    client = boto3.client("secretsmanager", region_name="us-east-1")
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])

secrets = get_secret("prs-ai-hub/production")
GROQ_API_KEY = secrets["GROQ_API_KEY"]
```
