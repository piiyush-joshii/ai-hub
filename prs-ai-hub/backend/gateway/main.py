import os
from contextlib import asynccontextmanager

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import ccr, enterprise, fixtures, pilot, prs
from services.database import init_db

load_dotenv(Path(__file__).resolve().parents[2] / ".env")  # prs-ai-hub/.env


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="PRS AI Hub — Gateway",
    description="Healthcare Purchase Request & Contract Validation System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prs.router, prefix="/api/v1/prs", tags=["PRS"])
app.include_router(ccr.router, prefix="/api/v1/ccr", tags=["CCR"])
app.include_router(enterprise.router, prefix="/api/v1/enterprise", tags=["Enterprise"])
app.include_router(pilot.router, prefix="/api/v1/pilot", tags=["Pilot"])
app.include_router(fixtures.router, prefix="/api/v1/fixtures", tags=["Fixtures"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "prs-gateway"}
