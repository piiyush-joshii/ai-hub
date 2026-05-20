from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import commercial, legal, parties

app = FastAPI(title="PRS Contract Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(parties.router)
app.include_router(commercial.router)
app.include_router(legal.router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "contract-agent", "port": 8002}
