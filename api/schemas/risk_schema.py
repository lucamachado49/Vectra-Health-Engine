"""
api/schemas/risk_schema.py — Schemas Pydantic para endpoints de risco e predição.

Usado por:
    api/routers/risk.py
    api/routers/municipalities.py
    api/services/prediction_service.py
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    project: str
    version: str
    model_loaded: bool
    latest_snapshot_loaded: bool


class MunicipalityResponse(BaseModel):
    geocode: str
    municipio: Optional[str] = None
    uf: Optional[str] = None


class RiskResponse(BaseModel):
    geocode: str
    municipio: Optional[str] = None
    ano: Optional[int] = None
    semana_epidemiologica: Optional[int] = None
    casos_dengue: Optional[float] = None
    incidencia_100k: Optional[float] = None
    environmental_risk_score: Optional[float] = None
    risco_ambiental_label: Optional[str] = None
    temp_media_7d: Optional[float] = None
    chuva_acumulada_7d: Optional[float] = None
    umidade_media_7d: Optional[float] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    ndvi_mean: Optional[float] = None
    ndwi_mean: Optional[float] = None
    water_area_pct: Optional[float] = None
    vegetation_area_pct: Optional[float] = None
    critical_area_pct: Optional[float] = None
    heat_island_score: Optional[float] = None
    leitos_ocupacao_pct: Optional[float] = None
    saneamento_risco: Optional[float] = None
    mobilidade_fluxo_score: Optional[float] = None
    social_signal_score: Optional[float] = None


class TimelineEvent(BaseModel):
    week: str
    label: str
    detail: str
    severity: str = "medium"
    feature: Optional[str] = None
    value: Optional[float] = None


class CausalTimelineResponse(BaseModel):
    geocode: str
    municipio: Optional[str] = None
    model: str = "x_learner_causal_risk"
    events: list[TimelineEvent]


class ResilienceGraphResponse(BaseModel):
    geocode: str
    municipio: Optional[str] = None
    nodes: list[dict[str, Any]]
    links: list[dict[str, Any]]


class CopilotQueryRequest(BaseModel):
    geocode: str
    question: str


class CopilotQueryResponse(BaseModel):
    geocode: str
    municipio: Optional[str] = None
    answer: str
    citations: list[str] = Field(default_factory=list)


class PredictionRequest(BaseModel):
    geocode: str = Field(..., description="Código IBGE do município.")
    ano: Optional[int] = Field(None, description="Ano. Se ausente, usa a linha mais recente.")
    semana_epidemiologica: Optional[int] = Field(None, description="Semana epidemiológica.")


class PredictionResponse(BaseModel):
    geocode: str
    municipio: Optional[str] = None
    ano: Optional[int] = None
    semana_epidemiologica: Optional[int] = None
    predicted_class: int
    probability_surto: Optional[float] = None
    risk_label: str
    model_name: Optional[str] = None
    top_context_factors: list[str]


class RecommendationRequest(BaseModel):
    geocode: str
    probability_surto: Optional[float] = None
    risk_label: Optional[str] = None
    municipio: Optional[str] = None
    include_message_template: bool = True


class RecommendationResponse(BaseModel):
    geocode: str
    municipio: Optional[str] = None
    risk_label: str
    probability_surto: Optional[float] = None
    priority_level: str
    technical_summary: str
    recommended_actions: list[str]
    message_template: Optional[str] = None
    requires_human_approval: bool = True
