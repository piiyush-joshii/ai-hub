from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import decide

app = FastAPI(title="PRS CCR Decision Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(decide.router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "ccr-agent", "port": 8004}
