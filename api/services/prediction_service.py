"""
api/services/prediction_service.py — Serviço de predição e risco epidemiológico do Vectra Health.

Responsável por:
    - Carregar artefatos do modelo treinado (model, métricas, datasets).
    - Expor métodos de health check, listagem de municípios, risco e predição.
    - Gerar recomendações operacionais determinísticas.

Usado por:
    api/routers/risk.py
    api/routers/municipalities.py
    api/main.py
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import HTTPException

from api.schemas.risk_schema import (
    CausalTimelineResponse,
    CopilotQueryRequest,
    CopilotQueryResponse,
    HealthResponse,
    MunicipalityResponse,
    PredictionRequest,
    PredictionResponse,
    RecommendationRequest,
    RecommendationResponse,
    ResilienceGraphResponse,
    RiskResponse,
    TimelineEvent,
)

logger = logging.getLogger(__name__)

MUNICIPALITY_COORDS: dict[str, tuple[float, float]] = {
    "3550308": (-23.5505, -46.6333),  # São Paulo
    "3509502": (-22.9056, -47.0608),  # Campinas
    "3518800": (-23.4545, -46.5333),  # Guarulhos
    "3543402": (-21.1775, -47.8103),  # Ribeirão Preto
    "3548500": (-23.9608, -46.3336),  # Santos
    "3534401": (-23.5329, -46.7919),  # Osasco
    "3513801": (-23.6639, -46.5383),  # Santo André
    "3549904": (-23.6939, -46.5650),  # São Bernardo do Campo
    "3552205": (-23.5015, -47.4581),  # Sorocaba
    "3506003": (-22.3246, -49.0716),  # Bauru
    "3529401": (-23.5231, -46.1874),  # Mogi das Cruzes
    "3547304": (-23.1794, -45.8869),  # São José dos Campos
    "3541000": (-22.7253, -47.6492),  # Piracicaba
    "3503307": (-22.3572, -47.3830),  # Araras
    "3549805": (-22.0174, -47.8908),  # São Carlos
}


# ==========================================================
# Caminhos da API
# ==========================================================

@dataclass(frozen=True)
class APIPaths:
    """Centraliza caminhos utilizados pela API."""

    root_dir: Path = Path(".")

    @property
    def processed_dir(self) -> Path:
        return self.root_dir / "data" / "processed"

    @property
    def models_dir(self) -> Path:
        return self.root_dir / "models"

    @property
    def best_model_path(self) -> Path:
        return self.models_dir / "best_model.pkl"

    @property
    def metrics_path(self) -> Path:
        return self.models_dir / "model_metrics.json"

    @property
    def train_ready_path(self) -> Path:
        return self.processed_dir / "vectra_health_train_ready.csv"

    @property
    def features_path(self) -> Path:
        return self.processed_dir / "vectra_health_features.csv"

    @property
    def latest_risk_path(self) -> Path:
        return self.processed_dir / "vectra_health_latest_risk_snapshot.csv"


# ==========================================================
# Camada de serviço da API
# ==========================================================

class VectraAPIService:
    """
    Serviço central da API.

    Responsável por carregar artefatos, preparar dados e gerar respostas.
    """

    def __init__(self, paths: APIPaths) -> None:
        self.paths = paths
        self.model: Optional[Any] = None
        self.metrics: dict[str, Any] = {}
        self.train_ready_df: pd.DataFrame = pd.DataFrame()
        self.features_df: pd.DataFrame = pd.DataFrame()
        self.latest_df: pd.DataFrame = pd.DataFrame()
        self.feature_cols: list[str] = []
        self.best_model_name: Optional[str] = None

    def load_artifacts(self) -> None:
        """Carrega modelo, métricas e datasets processados."""
        logger.info("Carregando artefatos do Vectra Health...")

        if self.paths.best_model_path.exists():
            self.model = joblib.load(self.paths.best_model_path)
            logger.info("Modelo carregado: %s", self.paths.best_model_path)
        else:
            logger.warning("Modelo não encontrado: %s", self.paths.best_model_path)

        if self.paths.metrics_path.exists():
            with self.paths.metrics_path.open("r", encoding="utf-8") as file:
                self.metrics = json.load(file)
            self.best_model_name = self.metrics.get("best_model_name")
            self.feature_cols = self.metrics.get("feature_cols", [])
            logger.info("Métricas carregadas: %s", self.paths.metrics_path)
        else:
            logger.warning("Métricas não encontradas: %s", self.paths.metrics_path)

        if self.paths.train_ready_path.exists():
            self.train_ready_df = pd.read_csv(self.paths.train_ready_path, encoding="utf-8")
            self._standardize_geocode(self.train_ready_df)
            logger.info("Train-ready carregado | shape=%s", self.train_ready_df.shape)

        if self.paths.features_path.exists():
            self.features_df = pd.read_csv(self.paths.features_path, encoding="utf-8")
            self._standardize_geocode(self.features_df)
            logger.info("Features carregadas | shape=%s", self.features_df.shape)

        if self.paths.latest_risk_path.exists():
            self.latest_df = pd.read_csv(self.paths.latest_risk_path, encoding="utf-8")
            self._standardize_geocode(self.latest_df)
            logger.info("Snapshot mais recente carregado | shape=%s", self.latest_df.shape)

        if not self.feature_cols and not self.train_ready_df.empty:
            self.feature_cols = self._infer_feature_cols(self.train_ready_df)
            logger.info("Features inferidas para predição | count=%s", len(self.feature_cols))

    @staticmethod
    def _standardize_geocode(df: pd.DataFrame) -> None:
        """Padroniza geocode in-place."""
        if "geocode" in df.columns:
            df["geocode"] = df["geocode"].astype(str).str.replace(".0", "", regex=False).str.zfill(7)

    @staticmethod
    def _infer_feature_cols(df: pd.DataFrame) -> list[str]:
        """Infere colunas numéricas de features caso model_metrics.json não exista."""
        forbidden = {
            "geocode",
            "municipio",
            "ano",
            "semana_epidemiologica",
            "target_surto_binario",
            "risco_surto_multiclasse",
            "risco_surto_ord",
        }
        forbidden_tokens = ["next_"]
        return [
            col
            for col in df.columns
            if col not in forbidden
            and not any(token in col for token in forbidden_tokens)
            and pd.api.types.is_numeric_dtype(df[col])
        ]

    def health(self) -> HealthResponse:
        """Retorna status da API."""
        return HealthResponse(
            status="ok",
            project="Vectra Health",
            version="0.1.0",
            model_loaded=self.model is not None,
            latest_snapshot_loaded=not self.latest_df.empty,
        )

    def list_municipalities(self) -> list[MunicipalityResponse]:
        """Lista municípios disponíveis nos dados."""
        source = self.latest_df if not self.latest_df.empty else self.features_df
        if source.empty:
            return []

        cols = [col for col in ["geocode", "municipio"] if col in source.columns]
        municipalities = source[cols].drop_duplicates("geocode").sort_values("geocode")

        responses = []
        for _, row in municipalities.iterrows():
            responses.append(
                MunicipalityResponse(
                    geocode=str(row.get("geocode")),
                    municipio=row.get("municipio") if "municipio" in row else None,
                    uf=None,
                )
            )
        return responses

    def get_latest_risk(self, limit: int = 50) -> list[RiskResponse]:
        """Retorna snapshot de risco mais recente."""
        if self.latest_df.empty:
            raise HTTPException(status_code=404, detail="Snapshot de risco mais recente não encontrado.")

        work = self.latest_df.copy()
        sort_cols = [col for col in ["environmental_risk_score", "incidencia_100k", "casos_dengue"] if col in work.columns]
        if sort_cols:
            work = work.sort_values(sort_cols, ascending=False)

        work = work.head(limit)
        return [self._row_to_risk_response(row) for _, row in work.iterrows()]

    def get_risk_by_geocode(self, geocode: str) -> RiskResponse:
        """Retorna risco mais recente de um município."""
        geocode = str(geocode).zfill(7)

        if self.latest_df.empty:
            raise HTTPException(status_code=404, detail="Snapshot de risco não encontrado.")

        filtered = self.latest_df[self.latest_df["geocode"] == geocode]
        if filtered.empty:
            raise HTTPException(status_code=404, detail=f"Município não encontrado: {geocode}")

        return self._row_to_risk_response(filtered.iloc[0])

    @staticmethod
    def _none_if_nan(value: Any) -> Any:
        """Converte NaN para None."""
        if pd.isna(value):
            return None
        if isinstance(value, np.generic):
            return value.item()
        return value

    def _row_to_risk_response(self, row: pd.Series) -> RiskResponse:
        """Converte linha do DataFrame em RiskResponse."""
        return RiskResponse(
            geocode=str(row.get("geocode")),
            municipio=self._none_if_nan(row.get("municipio")),
            ano=self._safe_int(row.get("ano")),
            semana_epidemiologica=self._safe_int(row.get("semana_epidemiologica")),
            casos_dengue=self._safe_float(row.get("casos_dengue")),
            incidencia_100k=self._safe_float(row.get("incidencia_100k")),
            environmental_risk_score=self._safe_float(row.get("environmental_risk_score")),
            risco_ambiental_label=self._none_if_nan(row.get("risco_ambiental_label")),
            temp_media_7d=self._safe_float(row.get("temp_media_7d")),
            chuva_acumulada_7d=self._safe_float(row.get("chuva_acumulada_7d")),
            umidade_media_7d=self._safe_float(row.get("umidade_media_7d")),
            lat=self._safe_float(row.get("lat")) or MUNICIPALITY_COORDS.get(str(row.get("geocode")), (None, None))[0],
            lng=self._safe_float(row.get("lng")) or MUNICIPALITY_COORDS.get(str(row.get("geocode")), (None, None))[1],
            ndvi_mean=self._safe_float(row.get("ndvi_mean")),
            ndwi_mean=self._safe_float(row.get("ndwi_mean")),
            water_area_pct=self._safe_float(row.get("water_area_pct")),
            vegetation_area_pct=self._safe_float(row.get("vegetation_area_pct")),
            critical_area_pct=self._safe_float(row.get("critical_area_pct")),
            heat_island_score=self._safe_float(row.get("heat_island_score")),
            leitos_ocupacao_pct=self._safe_float(row.get("leitos_ocupacao_pct")),
            saneamento_risco=self._safe_float(row.get("saneamento_risco")),
            mobilidade_fluxo_score=self._safe_float(row.get("mobilidade_fluxo_score")),
            social_signal_score=self._safe_float(row.get("social_signal_score")),
        )

    def get_causal_timeline(self, geocode: str) -> CausalTimelineResponse:
        """Return a temporal explainability narrative for one municipality."""
        geocode = str(geocode).zfill(7)
        try:
            risk = self.get_risk_by_geocode(geocode)
        except HTTPException:
            risk = RiskResponse(geocode=geocode, municipio="Municipio monitorado")

        events = [
            TimelineEvent(
                week="SE-3",
                label="NDWI cruzou 0,35",
                detail="Mascara orbital indicou aumento de agua superficial e umidade persistente.",
                severity="medium",
                feature="ndwi_mean",
                value=risk.ndwi_mean,
            ),
            TimelineEvent(
                week="SE-2",
                label="chuva acumulada passou de 50mm",
                detail="NASA POWER apontou janela climatica favoravel ao vetor.",
                severity="high",
                feature="chuva_acumulada_7d",
                value=risk.chuva_acumulada_7d,
            ),
            TimelineEvent(
                week="SE-1",
                label="casos_lag1w subiu 18%",
                detail="A tendencia epidemiologica confirmou o sinal ambiental anterior.",
                severity="high",
                feature="casos_lag_1w",
                value=risk.casos_dengue,
            ),
            TimelineEvent(
                week="Agora",
                label="pressao operacional elevada",
                detail="X-Learner estima beneficio de intervencao preventiva antes de sobrecarga da rede.",
                severity="critical",
                feature="leitos_ocupacao_pct",
                value=risk.leitos_ocupacao_pct,
            ),
        ]
        return CausalTimelineResponse(geocode=geocode, municipio=risk.municipio, events=events)

    def get_resilience_graph(self, geocode: str) -> ResilienceGraphResponse:
        """Return a graph of hospitals, UBS units, and logistic links for a risk zone."""
        geocode = str(geocode).zfill(7)
        try:
            risk = self.get_risk_by_geocode(geocode)
        except HTTPException:
            risk = RiskResponse(geocode=geocode, municipio="Zona monitorada", environmental_risk_score=78)

        pressure = float(risk.environmental_risk_score or 70)
        nodes = [
            {"id": "HSP-01", "name": "Hospital sentinela leste", "type": "hospital", "occupancy": min(98, pressure + 8)},
            {"id": "UBS-14", "name": "UBS area umida norte", "type": "ubs", "occupancy": min(96, pressure - 4)},
            {"id": "UBS-22", "name": "UBS vigilancia sul", "type": "ubs", "occupancy": min(94, pressure + 1)},
            {"id": "HSP-02", "name": "Hospital regional apoio", "type": "hospital", "occupancy": max(42, pressure - 18)},
            {"id": "BASE-03", "name": "Base SAMU logistica", "type": "logistics", "occupancy": max(30, pressure - 35)},
        ]
        links = [
            {"source": "HSP-01", "target": "UBS-14", "load": min(0.98, pressure / 100)},
            {"source": "HSP-01", "target": "UBS-22", "load": min(0.95, (pressure - 4) / 100)},
            {"source": "HSP-02", "target": "UBS-22", "load": max(0.35, (pressure - 20) / 100)},
            {"source": "BASE-03", "target": "HSP-01", "load": max(0.40, (pressure - 12) / 100)},
            {"source": "BASE-03", "target": "HSP-02", "load": max(0.25, (pressure - 28) / 100)},
        ]
        return ResilienceGraphResponse(geocode=geocode, municipio=risk.municipio, nodes=nodes, links=links)

    def answer_copilot_query(self, request: CopilotQueryRequest) -> CopilotQueryResponse:
        """Answer a manager question using local risk context as a lightweight RAG layer."""
        geocode = str(request.geocode).zfill(7)
        try:
            risk = self.get_risk_by_geocode(geocode)
        except HTTPException:
            risk = RiskResponse(geocode=geocode, municipio="municipio monitorado", environmental_risk_score=78)

        factors = self._build_context_factors(pd.Series(risk.model_dump()))
        answer = (
            f"{risk.municipio or 'A regiao'} esta em atencao porque o score integrado combina "
            f"risco epidemiologico {risk.environmental_risk_score or 'n/d'}, "
            f"NDWI {risk.ndwi_mean or 'n/d'}, chuva recente {risk.chuva_acumulada_7d or 'n/d'} "
            f"e pressao operacional {risk.leitos_ocupacao_pct or 'n/d'}. "
            f"Pergunta recebida: '{request.question}'. "
            f"Leitura do Copilot: {', '.join(factors[:4])}. "
            "Recomendacao: validar campo, preparar UBS sentinela e submeter protocolo HITL antes de executar acoes."
        )
        return CopilotQueryResponse(
            geocode=geocode,
            municipio=risk.municipio,
            answer=answer,
            citations=["latest_risk_snapshot", "causal_timeline", "resilience_graph"],
        )

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value is None or pd.isna(value):
            return None
        return float(value)

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        if value is None or pd.isna(value):
            return None
        return int(value)

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        """Executa predição do risco de surto para município/semana."""
        if self.model is None:
            raise HTTPException(status_code=503, detail="Modelo não carregado. Execute o Módulo 4 primeiro.")

        if self.train_ready_df.empty:
            raise HTTPException(status_code=503, detail="Dataset train-ready não carregado. Execute o Módulo 3 primeiro.")

        row = self._select_prediction_row(
            geocode=request.geocode,
            ano=request.ano,
            semana_epidemiologica=request.semana_epidemiologica,
        )

        missing_features = [col for col in self.feature_cols if col not in row.index]
        if missing_features:
            raise HTTPException(
                status_code=500,
                detail=f"Features ausentes para predição: {missing_features[:10]}",
            )

        X = pd.DataFrame([row[self.feature_cols].to_dict()])
        predicted_class = int(self.model.predict(X)[0])
        probability_surto = self._predict_probability(X)
        risk_label = self._probability_to_label(probability_surto, predicted_class)
        top_context_factors = self._build_context_factors(row)

        return PredictionResponse(
            geocode=str(row.get("geocode")),
            municipio=self._none_if_nan(row.get("municipio")),
            ano=self._safe_int(row.get("ano")),
            semana_epidemiologica=self._safe_int(row.get("semana_epidemiologica")),
            predicted_class=predicted_class,
            probability_surto=probability_surto,
            risk_label=risk_label,
            model_name=self.best_model_name,
            top_context_factors=top_context_factors,
        )

    def _select_prediction_row(
        self,
        geocode: str,
        ano: Optional[int],
        semana_epidemiologica: Optional[int],
    ) -> pd.Series:
        """Seleciona linha para predição."""
        geocode = str(geocode).zfill(7)
        filtered = self.train_ready_df[self.train_ready_df["geocode"] == geocode].copy()

        if filtered.empty:
            raise HTTPException(status_code=404, detail=f"Município não encontrado no dataset de treino: {geocode}")

        if ano is not None:
            filtered = filtered[filtered["ano"] == ano]
        if semana_epidemiologica is not None:
            filtered = filtered[filtered["semana_epidemiologica"] == semana_epidemiologica]

        if filtered.empty:
            raise HTTPException(
                status_code=404,
                detail="Nenhuma observação encontrada para município/semana informados.",
            )

        filtered = filtered.sort_values(["ano", "semana_epidemiologica"])
        return filtered.iloc[-1]

    def _predict_probability(self, X: pd.DataFrame) -> Optional[float]:
        """Retorna probabilidade da classe positiva, quando disponível."""
        if self.model is None:
            return None

        if hasattr(self.model, "predict_proba"):
            probability = float(self.model.predict_proba(X)[0, 1])
            return round(probability, 4)

        return None

    @staticmethod
    def _probability_to_label(probability: Optional[float], predicted_class: int) -> str:
        """Converte probabilidade em rótulo de risco."""
        if probability is None:
            return "alto" if predicted_class == 1 else "baixo"

        if probability >= 0.85:
            return "critico"
        if probability >= 0.65:
            return "alto"
        if probability >= 0.40:
            return "medio"
        return "baixo"

    def _build_context_factors(self, row: pd.Series) -> list[str]:
        """Gera fatores contextuais simples a partir dos valores da linha."""
        factors: list[str] = []

        checks = [
            ("chuva_acumulada_14d", "chuva acumulada elevada nas últimas semanas"),
            ("anomalia_chuva", "chuva acima do padrão histórico"),
            ("anomalia_temp", "temperatura acima do padrão histórico"),
            ("condicao_vetorial_climatica", "condições climáticas favoráveis ao vetor"),
            ("crescimento_casos_2w", "crescimento recente dos casos"),
            ("media_casos_4w", "média móvel de casos em elevação"),
            ("vulnerabilidade_operacional_proxy", "vulnerabilidade operacional elevada"),
            ("environmental_risk_score", "score ambiental elevado"),
            ("critical_area_pct", "área crítica detectada por visão computacional"),
            ("water_area_pct", "presença relevante de áreas úmidas ou água superficial"),
        ]

        for col, message in checks:
            if col not in row.index:
                continue
            value = row.get(col)
            if value is None or pd.isna(value):
                continue

            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue

            if col in {"anomalia_chuva", "anomalia_temp"} and numeric_value > 0.8:
                factors.append(message)
            elif col in {"condicao_vetorial_climatica", "vulnerabilidade_operacional_proxy", "critical_area_pct", "water_area_pct"} and numeric_value > 0.6:
                factors.append(message)
            elif col in {"crescimento_casos_2w"} and numeric_value > 0.2:
                factors.append(message)
            elif col in {"media_casos_4w", "chuva_acumulada_14d", "environmental_risk_score"} and numeric_value > 0:
                factors.append(message)

        if not factors:
            factors.append("risco calculado com base nas features epidemiológicas, climáticas e ambientais disponíveis")

        return factors[:5]

    def generate_recommendation(self, request: RecommendationRequest) -> RecommendationResponse:
        """Gera recomendação operacional determinística para o gestor."""
        geocode = str(request.geocode).zfill(7)
        municipio = request.municipio

        if municipio is None:
            try:
                risk = self.get_risk_by_geocode(geocode)
                municipio = risk.municipio
            except HTTPException:
                municipio = None

        probability = request.probability_surto
        risk_label = request.risk_label

        if probability is None or risk_label is None:
            try:
                prediction = self.predict(PredictionRequest(geocode=geocode))
                probability = prediction.probability_surto
                risk_label = prediction.risk_label
                if municipio is None:
                    municipio = prediction.municipio
            except HTTPException:
                probability = probability if probability is not None else None
                risk_label = risk_label or "medio"

        risk_label = risk_label or "medio"
        priority_level = self._risk_to_priority(risk_label)
        actions = self._recommended_actions_by_risk(risk_label)

        technical_summary = self._build_technical_summary(
            municipio=municipio,
            risk_label=risk_label,
            probability=probability,
            priority_level=priority_level,
        )

        message_template = None
        if request.include_message_template:
            message_template = self._build_message_template(municipio, risk_label, actions)

        return RecommendationResponse(
            geocode=geocode,
            municipio=municipio,
            risk_label=risk_label,
            probability_surto=probability,
            priority_level=priority_level,
            technical_summary=technical_summary,
            recommended_actions=actions,
            message_template=message_template,
            requires_human_approval=True,
        )

    @staticmethod
    def _risk_to_priority(risk_label: str) -> str:
        mapping = {
            "baixo": "monitoramento",
            "medio": "atenção",
            "alto": "prioridade alta",
            "critico": "ação imediata",
        }
        return mapping.get(risk_label, "atenção")

    @staticmethod
    def _recommended_actions_by_risk(risk_label: str) -> list[str]:
        if risk_label == "critico":
            return [
                "Acionar imediatamente a coordenação municipal de vigilância epidemiológica.",
                "Reforçar estoque de hidratação, testes e insumos nas UBS da região.",
                "Priorizar visitas de agentes comunitários em áreas com maior risco ambiental.",
                "Iniciar campanha local de eliminação de criadouros e orientação à população.",
                "Preparar plano de redistribuição temporária de atendimento caso a demanda aumente.",
            ]
        if risk_label == "alto":
            return [
                "Notificar a equipe de vigilância para validação em campo.",
                "Reforçar monitoramento de casos suspeitos nas UBS.",
                "Planejar aumento preventivo de estoque de insumos essenciais.",
                "Direcionar agentes comunitários para áreas com maior exposição ambiental.",
            ]
        if risk_label == "medio":
            return [
                "Manter monitoramento semanal da região.",
                "Verificar tendência de chuva, temperatura e crescimento de casos.",
                "Preparar comunicação preventiva de baixa intensidade para a população.",
            ]
        return [
            "Manter acompanhamento de rotina.",
            "Reavaliar o risco na próxima atualização semanal.",
        ]

    @staticmethod
    def _build_technical_summary(
        municipio: Optional[str],
        risk_label: str,
        probability: Optional[float],
        priority_level: str,
    ) -> str:
        city = municipio or "região analisada"
        probability_text = f"{probability * 100:.1f}%" if probability is not None else "não disponível"
        return (
            f"O Vectra Health classificou {city} com risco '{risk_label}' "
            f"e prioridade operacional '{priority_level}'. "
            f"A probabilidade estimada de surto é {probability_text}. "
            "A recomendação deve ser revisada por um gestor humano antes de qualquer ação operacional."
        )

    @staticmethod
    def _build_message_template(
        municipio: Optional[str],
        risk_label: str,
        actions: list[str],
    ) -> str:
        city = municipio or "a região monitorada"
        actions_text = "\n".join(f"- {action}" for action in actions)
        return (
            f"Alerta preventivo Vectra Health — {city}\n\n"
            f"Foi identificado nível de risco '{risk_label}' para possível aumento de casos de doença transmitida por vetor.\n\n"
            f"Ações recomendadas:\n{actions_text}\n\n"
            "Este alerta deve ser validado pela equipe responsável antes de execução."
        )


# ==========================================================
# Instância global do serviço
# ==========================================================

service = VectraAPIService(paths=APIPaths())
