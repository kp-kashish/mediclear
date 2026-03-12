from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import configure_logging
from app.api.v1.endpoints.reports import router as reports_router

configure_logging()

app = FastAPI(
    title="MediClear API",
    version="0.1.0",
    description="Privacy-first AI agent for medical lab report analysis",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])