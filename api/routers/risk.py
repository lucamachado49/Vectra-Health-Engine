"""Risk and prediction endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Query

from api.schemas.risk_schema import (
    CausalTimelineResponse,
    CopilotQueryRequest,
    CopilotQueryResponse,
    PredictionRequest,
    PredictionResponse,
    RecommendationRequest,
    RecommendationResponse,
    ResilienceGraphResponse,
    RiskResponse,
)
from api.services.prediction_service import service

router = APIRouter(tags=["risk"])


@router.get("/risk/latest", response_model=list[RiskResponse])
def latest_risk(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of regions returned."),
) -> list[RiskResponse]:
    """Return the latest risk snapshot ranked by risk indicators."""
    return service.get_latest_risk(limit=limit)


@router.get("/risk/{geocode}", response_model=RiskResponse)
def risk_by_geocode(geocode: str) -> RiskResponse:
    """Return the latest risk record for one municipality."""
    return service.get_risk_by_geocode(geocode)


@router.get("/risk/{geocode}/timeline", response_model=CausalTimelineResponse)
def risk_timeline(geocode: str) -> CausalTimelineResponse:
    """Return temporal explainability events for one municipality."""
    return service.get_causal_timeline(geocode)


@router.get("/risk/{geocode}/resilience-graph", response_model=ResilienceGraphResponse)
def resilience_graph(geocode: str) -> ResilienceGraphResponse:
    """Return the health logistics resilience graph for a risk zone."""
    return service.get_resilience_graph(geocode)


@router.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    """Run the trained model for a municipality/week."""
    return service.predict(request)


@router.post("/agent/recommendation", response_model=RecommendationResponse)
def agent_recommendation(request: RecommendationRequest) -> RecommendationResponse:
    """Generate a deterministic operational recommendation from risk data."""
    return service.generate_recommendation(request)


@router.post("/copilot/query", response_model=CopilotQueryResponse)
def copilot_query(request: CopilotQueryRequest) -> CopilotQueryResponse:
    """Answer a natural language question over spatial and epidemiological context."""
    return service.answer_copilot_query(request)
