"""LLM Agent endpoints with human-in-the-loop review."""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Query

from api.schemas.agent_schema import (
    AgentRecommendationRequest,
    HumanReviewRecord,
    HumanReviewRequest,
    OperationalProtocol,
)
from api.services.llm_agent_service import VectraLLMAgentService

router = APIRouter(prefix="/llm-agent", tags=["llm-agent"])


@lru_cache(maxsize=1)
def get_agent_service() -> VectraLLMAgentService:
    """Create the agent service lazily so imports stay side-effect-light."""
    return VectraLLMAgentService()


@router.post("/protocol", response_model=OperationalProtocol)
def generate_protocol(request: AgentRecommendationRequest) -> OperationalProtocol:
    """Generate an operational protocol for human review."""
    return get_agent_service().generate_protocol(request)


@router.post("/review", response_model=HumanReviewRecord)
def register_review(request: HumanReviewRequest) -> HumanReviewRecord:
    """Register a human decision over a generated protocol."""
    return get_agent_service().register_human_review(request)


@router.get("/protocols")
def list_protocols(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of protocols returned."),
) -> list[dict[str, Any]]:
    """List recently generated protocols."""
    return get_agent_service().list_protocols(limit=limit)


@router.get("/reviews")
def list_reviews(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of reviews returned."),
) -> list[dict[str, Any]]:
    """List recently registered human reviews."""
    return get_agent_service().list_reviews(limit=limit)


@router.get("/execution/{protocol_id}")
def autonomous_execution(protocol_id: str) -> dict[str, Any]:
    """Return a simulated autonomous execution trace after HITL approval."""
    return get_agent_service().simulate_autonomous_execution(protocol_id)
