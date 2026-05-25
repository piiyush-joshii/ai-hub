from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import requestor, vendor, vizient

app = FastAPI(title="PRS Intake Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(requestor.router)
app.include_router(vendor.router)
app.include_router(vizient.router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "intake-agent", "port": 8001}
