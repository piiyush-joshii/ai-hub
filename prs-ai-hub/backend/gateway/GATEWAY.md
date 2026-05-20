# GATEWAY.md — FastAPI Gateway Service Specification

> The gateway is the **single entry point** for the frontend.
> It handles auth, file parsing, request tracking, orchestration invocation, and DB persistence.
> Port: **8000**

---

## Dependencies

```bash
pip install fastapi uvicorn[standard] python-jose[cryptography] passlib[bcrypt] \
            python-multipart pdfplumber python-docx sqlalchemy[asyncio] asyncpg \
            alembic redis httpx langchain langgraph langchain-groq
```

---

## File Structure

```
backend/gateway/
├── main.py              # FastAPI app entry point
├── routers/
│   ├── prs.py           # PRS submission endpoints
│   ├── auth.py          # Login / token endpoints
│   └── admin.py         # Review queue, history endpoints
├── services/
│   ├── file_parser.py   # PDF/DOCX text extraction
│   ├── auth_service.py  # JWT logic
│   └── db_service.py    # PostgreSQL async operations
├── middleware/
│   └── audit.py         # Audit log middleware
├── orchestrator/        # LangGraph graph (imported here)
│   ├── graph.py
│   └── state.py
├── requirements.txt
└── Dockerfile
```

---

## Main App

```python
# backend/gateway/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import prs, auth, admin
import os

app = FastAPI(
    title="PRS AI Hub — Gateway",
    description="Healthcare Purchase Request & Contract Validation System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(prs.router, prefix="/api/v1/prs", tags=["PRS"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "prs-gateway"}
```

---

## Core Endpoints

### POST `/api/v1/prs/submit`
Submit a full PRS request for AI validation.

```
Request:  multipart/form-data
  - form_data: JSON string (PRSIntakeRequest fields)
  - contract_file: PDF or DOCX file
  - addendum_file: PDF or DOCX file (optional)

Response: 202 Accepted
  {
    "success": true,
    "request_id": "PRS-2026-A1B2C3D4",
    "message": "Validation in progress",
    "status_url": "/api/v1/prs/status/PRS-2026-A1B2C3D4"
  }
```

Processing flow:
1. Validate JWT token
2. Parse uploaded files → extract text
3. Generate `request_id`
4. Save to PostgreSQL with status = `pending`
5. Push to Redis queue for async processing
6. Return 202 immediately

### GET `/api/v1/prs/status/{request_id}`
Poll for validation results.

```
Response: 200 OK
  {
    "request_id": "PRS-2026-A1B2C3D4",
    "status": "pending | processing | complete | failed",
    "result": { ...OrchestratorResult... }   // null if still pending
  }
```

### WebSocket `/api/v1/prs/ws/{request_id}`
Real-time status updates — preferred over polling for frontend.

```
Messages sent to client:
  { "event": "agent_complete", "agent": "requestor_info", "status": "pass" }
  { "event": "agent_complete", "agent": "vendor_info", "status": "partial" }
  ...
  { "event": "validation_complete", "overall_status": "fail", "result": {...} }
```

### GET `/api/v1/prs/history`
Get paginated list of past submissions.

```
Query params: ?page=1&limit=20&status=fail&date_from=2026-01-01
Response: { "items": [...], "total": 45, "page": 1, "limit": 20 }
```

### GET `/api/v1/prs/{request_id}`
Get full details of a single PRS submission.

### POST `/api/v1/admin/review/{request_id}`
Mark a PRS request as reviewed by a human.

```
Body: { "decision": "approved | rejected", "notes": "Approved after legal review" }
```

---

## File Parser Service

```python
# backend/gateway/services/file_parser.py
import pdfplumber
from docx import Document
import io

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n\n".join(pages)

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX."""
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs)

def parse_uploaded_file(filename: str, file_bytes: bytes) -> str:
    """Route to correct parser based on file extension."""
    ext = filename.lower().split(".")[-1]
    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
```

---

## Auth Service

```python
# backend/gateway/services/auth_service.py
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 480))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

---

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## requirements.txt

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
pdfplumber==0.11.0
python-docx==1.1.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
alembic==1.13.1
redis==5.0.4
httpx==0.27.0
langgraph==0.1.0
langchain==0.2.0
langchain-groq==0.1.6
pydantic[email]==2.7.1
```
