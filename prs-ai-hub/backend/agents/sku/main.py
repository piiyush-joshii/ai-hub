from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import policy, schedule

app = FastAPI(title="PRS SKU Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schedule.router)
app.include_router(policy.router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "sku-agent", "port": 8003}
