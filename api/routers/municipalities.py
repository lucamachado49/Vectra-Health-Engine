"""Municipality endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from api.schemas.risk_schema import MunicipalityResponse
from api.services.prediction_service import service

router = APIRouter(tags=["municipalities"])


@router.get("/municipalities", response_model=list[MunicipalityResponse])
def municipalities() -> list[MunicipalityResponse]:
    """List municipalities available in the loaded datasets."""
    return service.list_municipalities()
