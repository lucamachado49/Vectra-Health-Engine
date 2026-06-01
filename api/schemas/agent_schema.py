"""
api/schemas/agent_schema.py — Schemas Pydantic para o LLM Agent com Human-in-the-Loop.

Usado por:
    api/routers/agent.py
    api/services/llm_agent_service.py
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

RiskLevel = Literal["baixo", "medio", "alto", "critico"]
DecisionStatus = Literal["pending_review", "approved", "rejected", "revision_requested"]


class RiskContext(BaseModel):
    """Contexto técnico enviado pelo modelo/API para o agente."""

    geocode: str = Field(..., description="Código IBGE do município ou região.")
    municipio: Optional[str] = Field(None)
    ano: Optional[int] = None
    semana_epidemiologica: Optional[int] = None
    risk_label: RiskLevel = Field(..., description="Classificação de risco.")
    probability_surto: Optional[float] = Field(None)
    casos_dengue: Optional[float] = None
    incidencia_100k: Optional[float] = None
    temp_media_7d: Optional[float] = None
    chuva_acumulada_7d: Optional[float] = None
    umidade_media_7d: Optional[float] = None
    environmental_risk_score: Optional[float] = None
    top_context_factors: list[str] = Field(default_factory=list)
    model_name: Optional[str] = None


class AgentRecommendationRequest(BaseModel):
    """Requisição para geração de protocolo pelo agente."""

    risk_context: RiskContext
    audience: Literal["gestor_saude", "ubs", "vigilancia_epidemiologica", "defesa_civil"] = "gestor_saude"
    tone: Literal["executivo", "tecnico", "operacional"] = "operacional"
    use_llm: bool = Field(default=True)


class OperationalProtocol(BaseModel):
    """Resposta estruturada gerada pelo agente."""

    protocol_id: str
    created_at: str
    geocode: str
    municipio: Optional[str]
    risk_label: RiskLevel
    probability_surto: Optional[float]
    status: DecisionStatus = "pending_review"
    title: str
    executive_summary: str
    technical_rationale: str
    recommended_actions: list[str]
    operational_checklist: list[str]
    message_to_health_units: str
    required_resources: list[str]
    human_approval_required: bool = True
    limitations: list[str]
    generated_by: str


class HumanReviewRequest(BaseModel):
    """Requisição para registrar decisão humana sobre um protocolo."""

    protocol_id: str
    decision: Literal["approved", "rejected", "revision_requested"]
    reviewer_name: Optional[str] = None
    reviewer_role: Optional[str] = None
    comments: Optional[str] = None


class HumanReviewRecord(BaseModel):
    """Registro de revisão humana."""

    protocol_id: str
    decision: Literal["approved", "rejected", "revision_requested"]
    reviewer_name: Optional[str]
    reviewer_role: Optional[str]
    comments: Optional[str]
    reviewed_at: str
