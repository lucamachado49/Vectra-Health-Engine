"""
Módulo 7 — LLM Agent com Human-in-the-Loop do Vectra Health

Caminhos recomendados no projeto:
    api/services/llm_agent_service.py
    api/routers/agent.py

Objetivo:
    Transformar previsões técnicas do modelo epidemiológico em recomendações operacionais
    estruturadas, explicáveis e revisáveis por um gestor humano.

Funções principais:
    1. Receber contexto de risco epidemiológico.
    2. Montar prompt técnico para um LLM.
    3. Gerar protocolo de contingência.
    4. Gerar mensagem para UBS/equipe de vigilância.
    5. Gerar checklist operacional.
    6. Exigir aprovação humana antes da execução.
    7. Registrar decisão: aprovado, rejeitado ou solicitado ajuste.

Dependências obrigatórias:
    pip install fastapi pydantic python-dotenv

Dependência opcional para uso real com LLM:
    pip install openai

Variáveis de ambiente opcionais:
    VECTRA_LLM_PROVIDER=nvidia|openai|openai_compatible
    VECTRA_LLM_API_KEY=<sua_chave>
    VECTRA_LLM_BASE_URL=https://integrate.api.nvidia.com/v1
    VECTRA_LLM_MODEL=meta/llama-3.3-70b-instruct

Observação:
    O módulo funciona mesmo sem chave de LLM, usando fallback determinístico.
    Isso garante que a entrega acadêmica continue executável sem depender de API externa.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

from api.schemas.agent_schema import (
    RiskLevel,
    DecisionStatus,
    RiskContext,
    AgentRecommendationRequest,
    OperationalProtocol,
    HumanReviewRequest,
    HumanReviewRecord,
)


# ==========================================================
# Logging
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ==========================================================
# Configuração
# ==========================================================

@dataclass(frozen=True)
class AgentPaths:
    """Caminhos utilizados pelo agente para logs e auditoria."""

    root_dir: Path = Path(".")

    @property
    def agent_logs_dir(self) -> Path:
        return self.root_dir / "data" / "processed" / "agent_logs"

    @property
    def protocols_path(self) -> Path:
        return self.agent_logs_dir / "protocols.jsonl"

    @property
    def reviews_path(self) -> Path:
        return self.agent_logs_dir / "human_reviews.jsonl"

    def create_all(self) -> None:
        self.agent_logs_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Diretório do agente verificado/criado: %s", self.agent_logs_dir)


@dataclass(frozen=True)
class LLMConfig:
    """Configuração do LLM."""

    provider: str = os.getenv("VECTRA_LLM_PROVIDER", "nvidia")
    model: str = os.getenv("VECTRA_LLM_MODEL", "meta/llama-3.3-70b-instruct")
    base_url: str = os.getenv("VECTRA_LLM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    temperature: float = 0.2
    max_tokens: int = 1200


# ==========================================================
# Serviço principal do agente
# ==========================================================

class VectraLLMAgentService:
    """
    Serviço de agente LLM com fallback determinístico e human-in-the-loop.
    """

    def __init__(
        self,
        paths: AgentPaths | None = None,
        llm_config: LLMConfig | None = None,
    ) -> None:
        self.paths = paths or AgentPaths(root_dir=Path("."))
        self.llm_config = llm_config or LLMConfig()
        self.paths.create_all()
        self.client = self._build_openai_client()

    def _build_openai_client(self) -> Optional[Any]:
        """Inicializa cliente OpenAI-compatible quando disponível."""
        provider = self.llm_config.provider.lower()
        api_key = (
            os.getenv("VECTRA_LLM_API_KEY")
            or os.getenv("NVIDIA_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )

        if not OPENAI_AVAILABLE:
            logger.warning("Pacote openai não instalado. Agente usará fallback determinístico.")
            return None

        if not api_key:
            logger.warning("Chave de LLM não encontrada. Agente usará fallback determinístico.")
            return None

        if provider == "openai":
            logger.info("Cliente OpenAI inicializado para o agente | model=%s", self.llm_config.model)
            return OpenAI(api_key=api_key)

        logger.info(
            "Cliente OpenAI-compatible inicializado | provider=%s | model=%s | base_url=%s",
            provider,
            self.llm_config.model,
            self.llm_config.base_url,
        )
        return OpenAI(api_key=api_key, base_url=self.llm_config.base_url)

    def generate_protocol(self, request: AgentRecommendationRequest) -> OperationalProtocol:
        """
        Gera protocolo operacional estruturado.

        Estratégia:
            1. Tenta usar LLM se solicitado e disponível.
            2. Se falhar, usa fallback determinístico.
            3. Salva protocolo em JSONL para auditoria.
        """
        if request.use_llm and self.client is not None:
            try:
                protocol = self._generate_with_llm(request)
                self._append_jsonl(self.paths.protocols_path, protocol.model_dump())
                return protocol
            except Exception as exc:  # noqa: BLE001
                logger.exception("Falha ao gerar protocolo com LLM. Usando fallback. Erro: %s", exc)

        protocol = self._generate_fallback_protocol(request)
        self._append_jsonl(self.paths.protocols_path, protocol.model_dump())
        return protocol

    def _generate_with_llm(self, request: AgentRecommendationRequest) -> OperationalProtocol:
        """Gera protocolo via LLM real."""
        if self.client is None:
            raise RuntimeError("Cliente LLM indisponível.")

        prompt = self._build_prompt(request)

        response = self.client.chat.completions.create(
            model=self.llm_config.model,
            temperature=self.llm_config.temperature,
            max_tokens=self.llm_config.max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um agente técnico de apoio à vigilância epidemiológica. "
                        "Sua função é transformar previsões de risco em protocolos operacionais claros, "
                        "seguros e revisáveis por humanos. Nunca afirme certeza absoluta. "
                        "Sempre indique que a recomendação precisa de validação humana. "
                        "Responda estritamente em JSON válido, sem markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM retornou conteúdo vazio.")

        parsed = json.loads(content)
        protocol = self._coerce_llm_json_to_protocol(parsed, request.risk_context)
        return protocol

    def _build_prompt(self, request: AgentRecommendationRequest) -> str:
        """Monta prompt estruturado para o LLM."""
        ctx = request.risk_context
        probability = (
            f"{ctx.probability_surto * 100:.1f}%" if ctx.probability_surto is not None else "não disponível"
        )

        return f"""
Gere um protocolo de contingência preventiva para o Vectra Health.

Contexto técnico:
- Município/região: {ctx.municipio or 'não informado'}
- Código geográfico: {ctx.geocode}
- Ano: {ctx.ano}
- Semana epidemiológica: {ctx.semana_epidemiologica}
- Nível de risco: {ctx.risk_label}
- Probabilidade estimada de surto: {probability}
- Casos de dengue: {ctx.casos_dengue}
- Incidência por 100 mil habitantes: {ctx.incidencia_100k}
- Temperatura média 7d: {ctx.temp_media_7d}
- Chuva acumulada 7d: {ctx.chuva_acumulada_7d}
- Umidade média 7d: {ctx.umidade_media_7d}
- Score ambiental: {ctx.environmental_risk_score}
- Fatores principais: {', '.join(ctx.top_context_factors) if ctx.top_context_factors else 'não informado'}
- Modelo utilizado: {ctx.model_name or 'não informado'}

Público-alvo: {request.audience}
Tom: {request.tone}

Gere JSON válido com exatamente estes campos:
{{
  "title": "string",
  "executive_summary": "string",
  "technical_rationale": "string",
  "recommended_actions": ["string"],
  "operational_checklist": ["string"],
  "message_to_health_units": "string",
  "required_resources": ["string"],
  "limitations": ["string"]
}}

Regras:
- Seja específico, mas não invente dados ausentes.
- Não diga que o surto certamente ocorrerá.
- Deixe claro que é uma recomendação preventiva baseada em modelo.
- Inclua aprovação humana obrigatória antes de execução.
- Recomendações devem ser compatíveis com saúde pública municipal.
""".strip()

    def _coerce_llm_json_to_protocol(
        self,
        payload: dict[str, Any],
        ctx: RiskContext,
    ) -> OperationalProtocol:
        """Converte JSON do LLM para OperationalProtocol."""
        protocol = OperationalProtocol(
            protocol_id=self._new_protocol_id(),
            created_at=self._now_iso(),
            geocode=ctx.geocode,
            municipio=ctx.municipio,
            risk_label=ctx.risk_label,
            probability_surto=ctx.probability_surto,
            status="pending_review",
            title=str(payload.get("title", "Protocolo preventivo Vectra Health")),
            executive_summary=str(payload.get("executive_summary", "Resumo não informado.")),
            technical_rationale=str(payload.get("technical_rationale", "Justificativa técnica não informada.")),
            recommended_actions=self._ensure_list(payload.get("recommended_actions")),
            operational_checklist=self._ensure_list(payload.get("operational_checklist")),
            message_to_health_units=str(payload.get("message_to_health_units", "Mensagem não informada.")),
            required_resources=self._ensure_list(payload.get("required_resources")),
            human_approval_required=True,
            limitations=self._ensure_list(payload.get("limitations")) or self._default_limitations(),
            generated_by=f"{self.llm_config.provider}:{self.llm_config.model}",
        )
        return protocol

    def _generate_fallback_protocol(self, request: AgentRecommendationRequest) -> OperationalProtocol:
        """Gera protocolo determinístico sem LLM externo."""
        ctx = request.risk_context
        city = ctx.municipio or "região monitorada"
        probability_text = (
            f"{ctx.probability_surto * 100:.1f}%" if ctx.probability_surto is not None else "não disponível"
        )
        risk = ctx.risk_label

        actions = self._actions_by_risk(risk)
        checklist = self._checklist_by_risk(risk)
        resources = self._resources_by_risk(risk)
        factors = ctx.top_context_factors or ["fatores epidemiológicos, climáticos e ambientais disponíveis"]

        technical_rationale = (
            f"O modelo classificou {city} com risco '{risk}' para aumento de casos. "
            f"A probabilidade estimada de surto é {probability_text}. "
            f"Os principais fatores associados ao alerta foram: {', '.join(factors[:5])}. "
            "A recomendação é preventiva e deve ser validada por equipe humana responsável."
        )

        message_to_health_units = (
            f"Alerta preventivo Vectra Health — {city}\n\n"
            f"Foi identificado nível de risco '{risk}' para possível aumento de casos de doença transmitida por vetor. "
            "Solicitamos revisão da coordenação responsável e preparação preventiva das equipes locais.\n\n"
            "Ações iniciais recomendadas:\n"
            + "\n".join(f"- {action}" for action in actions[:4])
            + "\n\nEste alerta requer validação humana antes de execução operacional."
        )

        return OperationalProtocol(
            protocol_id=self._new_protocol_id(),
            created_at=self._now_iso(),
            geocode=ctx.geocode,
            municipio=ctx.municipio,
            risk_label=risk,
            probability_surto=ctx.probability_surto,
            status="pending_review",
            title=f"Protocolo preventivo para risco {risk} — {city}",
            executive_summary=(
                f"O Vectra Health identificou risco '{risk}' em {city}. "
                "O sistema recomenda ações preventivas proporcionais ao risco, com revisão humana obrigatória."
            ),
            technical_rationale=technical_rationale,
            recommended_actions=actions,
            operational_checklist=checklist,
            message_to_health_units=message_to_health_units,
            required_resources=resources,
            human_approval_required=True,
            limitations=self._default_limitations(),
            generated_by="fallback:deterministic_rules",
        )

    @staticmethod
    def _actions_by_risk(risk: RiskLevel) -> list[str]:
        """Ações recomendadas por nível de risco."""
        if risk == "critico":
            return [
                "Acionar imediatamente a coordenação municipal de vigilância epidemiológica.",
                "Reforçar estoque de hidratação, testes, repelentes e insumos básicos nas UBS prioritárias.",
                "Direcionar agentes comunitários para vistorias em áreas com maior risco ambiental.",
                "Iniciar campanha local de eliminação de criadouros e orientação à população.",
                "Preparar plano de redistribuição temporária de atendimento caso a demanda aumente.",
                "Monitorar diariamente novos casos suspeitos durante o período crítico.",
            ]
        if risk == "alto":
            return [
                "Notificar a equipe de vigilância epidemiológica para validação em campo.",
                "Reforçar monitoramento de casos suspeitos nas UBS da região.",
                "Planejar aumento preventivo de estoque de insumos essenciais.",
                "Priorizar visitas de agentes comunitários em áreas com maior exposição ambiental.",
                "Preparar comunicação preventiva para a população local.",
            ]
        if risk == "medio":
            return [
                "Manter monitoramento semanal da região.",
                "Verificar evolução de chuva, temperatura, umidade e casos recentes.",
                "Preparar comunicação preventiva de baixa intensidade.",
                "Reavaliar o risco na próxima semana epidemiológica.",
            ]
        return [
            "Manter acompanhamento de rotina.",
            "Reavaliar risco em atualização semanal.",
            "Registrar estabilidade do cenário epidemiológico.",
        ]

    @staticmethod
    def _checklist_by_risk(risk: RiskLevel) -> list[str]:
        """Checklist operacional por risco."""
        base = [
            "Confirmar dados epidemiológicos mais recentes.",
            "Validar alerta com responsável técnico humano.",
            "Registrar decisão no sistema.",
        ]
        if risk in {"alto", "critico"}:
            return [
                "Revisar mapa de áreas críticas.",
                "Verificar disponibilidade de insumos nas UBS.",
                "Checar escala de agentes comunitários.",
                "Confirmar canais de comunicação com unidades de saúde.",
                "Definir responsáveis por execução e acompanhamento.",
            ] + base
        return base

    @staticmethod
    def _resources_by_risk(risk: RiskLevel) -> list[str]:
        """Recursos sugeridos por risco."""
        if risk == "critico":
            return [
                "kits de hidratação",
                "testes diagnósticos ou triagem clínica",
                "repelentes e materiais educativos",
                "equipe adicional de agentes comunitários",
                "canal de comunicação com UBS e vigilância",
            ]
        if risk == "alto":
            return [
                "materiais educativos",
                "estoque preventivo de insumos básicos",
                "equipe de vigilância para validação em campo",
            ]
        if risk == "medio":
            return [
                "monitoramento semanal",
                "comunicação preventiva básica",
            ]
        return ["rotina de monitoramento"]

    @staticmethod
    def _default_limitations() -> list[str]:
        """Limitações padrão do protocolo."""
        return [
            "A previsão é probabilística e não indica certeza de surto.",
            "Dados ausentes ou defasados podem afetar a qualidade da recomendação.",
            "A decisão operacional deve ser validada por profissional humano responsável.",
            "O sistema não substitui protocolos oficiais de vigilância epidemiológica.",
        ]

    def register_human_review(self, request: HumanReviewRequest) -> HumanReviewRecord:
        """Registra decisão humana sobre um protocolo."""
        record = HumanReviewRecord(
            protocol_id=request.protocol_id,
            decision=request.decision,
            reviewer_name=request.reviewer_name,
            reviewer_role=request.reviewer_role,
            comments=request.comments,
            reviewed_at=self._now_iso(),
        )
        self._append_jsonl(self.paths.reviews_path, record.model_dump())
        logger.info("Revisão humana registrada | protocol_id=%s | decision=%s", request.protocol_id, request.decision)
        return record

    def list_protocols(self, limit: int = 50) -> list[dict[str, Any]]:
        """Lista protocolos gerados mais recentes."""
        return self._read_jsonl_tail(self.paths.protocols_path, limit=limit)

    def list_reviews(self, limit: int = 50) -> list[dict[str, Any]]:
        """Lista revisões humanas mais recentes."""
        return self._read_jsonl_tail(self.paths.reviews_path, limit=limit)

    def simulate_autonomous_execution(self, protocol_id: str) -> dict[str, Any]:
        """Executa o grafo LangGraph real de contingência pós-aprovação HITL.

        Carrega o protocolo aprovado do log JSONL, reconstrói o contexto e
        invoca o StateGraph compilado. Retorna os steps para o terminal do frontend.
        """
        from api.services.langgraph_agent import run_contingency_graph  # noqa: PLC0415

        # Tenta recuperar contexto do protocolo salvo em disco
        geocode, municipio, risk_label, risk_score, probability, factors = (
            self._load_protocol_context(protocol_id)
        )

        result = run_contingency_graph(
            protocol_id=protocol_id,
            geocode=geocode,
            municipio=municipio,
            risk_label=risk_label,
            risk_score=risk_score,
            probability_surto=probability,
            top_factors=factors,
        )

        return {
            "protocol_id":   protocol_id,
            "engine":        "langgraph_real_runtime",
            "status":        "completed",
            "steps":         result.get("steps", []),
            "audit_hash":    result.get("audit_hash", ""),
            "alertas":       result.get("alertas_enviados", 0),
            "ubs":           result.get("ubs_reforçadas", []),
            "insumos":       result.get("insumos_redistribuidos", {}),
            "analise_llm":   result.get("analise_llm", ""),
        }

    def _load_protocol_context(
        self,
        protocol_id: str,
    ) -> tuple[str, str, str, float, float, list[str]]:
        """Reconstrói o contexto de risco a partir do protocolo salvo."""
        defaults = ("3550308", "São Paulo", "alto", 78.0, 0.78, ["condições climáticas e epidemiológicas"])

        try:
            entries = self._read_jsonl_tail(self.paths.protocols_path, limit=200)
            for entry in reversed(entries):
                if entry.get("protocol_id") == protocol_id:
                    geocode    = str(entry.get("geocode", defaults[0]))
                    municipio  = str(entry.get("municipio") or defaults[1])
                    risk_label = str(entry.get("risk_label", defaults[2]))
                    risk_score = float(entry.get("probability_surto") or 0.78) * 100
                    prob       = float(entry.get("probability_surto") or 0.78)
                    factors    = list(entry.get("recommended_actions", defaults[5])[:4])
                    return geocode, municipio, risk_label, risk_score, prob, factors
        except Exception as exc:  # noqa: BLE001
            logger.warning("Não foi possível carregar contexto do protocolo %s: %s", protocol_id, exc)

        return defaults

    @staticmethod
    def _ensure_list(value: Any) -> list[str]:
        """Garante que um campo seja lista de strings."""
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]

    @staticmethod
    def _new_protocol_id() -> str:
        return f"vectra-protocol-{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")

    @staticmethod
    def _read_jsonl_tail(path: Path, limit: int = 50) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        records = []
        for line in lines[-limit:]:
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records





# ==========================================================
# Execução local simples para teste sem FastAPI
# ==========================================================

if __name__ == "__main__":
    service = VectraLLMAgentService()

    sample_request = AgentRecommendationRequest(
        risk_context=RiskContext(
            geocode="3550308",
            municipio="São Paulo",
            ano=2025,
            semana_epidemiologica=12,
            risk_label="alto",
            probability_surto=0.78,
            casos_dengue=245.0,
            incidencia_100k=32.4,
            temp_media_7d=27.8,
            chuva_acumulada_7d=64.2,
            umidade_media_7d=81.5,
            environmental_risk_score=74.0,
            top_context_factors=[
                "chuva acumulada elevada nas últimas semanas",
                "temperatura acima do padrão histórico",
                "crescimento recente dos casos",
                "condições climáticas favoráveis ao vetor",
            ],
            model_name="random_forest",
        ),
        use_llm=False,
    )

    protocol = service.generate_protocol(sample_request)
    print(protocol.model_dump_json(indent=2))
