"""FastAPI entrypoint for the Vectra Health API."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import agent, execution, municipalities, risk
from api.schemas.risk_schema import HealthResponse
from api.services.prediction_service import service as prediction_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vectra Health API",
    description="API for epidemiological risk prediction and preventive decision support.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    """Load model and dataset artifacts once when the API starts."""
    prediction_service.load_artifacts()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return API health and artifact loading status."""
    return prediction_service.health()


app.include_router(municipalities.router)
app.include_router(risk.router)
app.include_router(agent.router)
app.include_router(execution.router)
