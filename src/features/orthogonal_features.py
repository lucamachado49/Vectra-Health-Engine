"""Feature engineering for orthogonal risk signals used by Vectra Health.

This module keeps non-epidemiological sources explicit:
- CNES/DataSUS operational pressure.
- SNIS sanitation fragility.
- mobility-driven spatial contagion.
- social sensor leading indicators.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def add_operational_capacity_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create DataSUS/CNES operational features."""
    work = df.copy()
    leitos = work.get("leitos_total", 0).replace(0, np.nan)
    ocupados = work.get("leitos_ocupados", 0)
    work["leitos_ocupacao_pct"] = (ocupados / leitos * 100).fillna(0).clip(0, 100)
    work["leitos_por_10k"] = (work.get("leitos_total", 0) / work.get("populacao", 1) * 10000).fillna(0)
    work["absenteismo_rede_pct"] = work.get("faltas_ubs", 0) / work.get("agendamentos_ubs", 1) * 100
    work["capacidade_resposta_saude"] = (
        0.45 * (100 - work["leitos_ocupacao_pct"])
        + 0.35 * work["leitos_por_10k"].clip(0, 50) * 2
        + 0.20 * (100 - work["absenteismo_rede_pct"].clip(0, 100))
    ).clip(0, 100)
    return work


def add_sanitation_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create SNIS features tied to vector-borne disease risk."""
    work = df.copy()
    regularidade = work.get("regularidade_abastecimento_pct", 95).clip(0, 100)
    coleta_esgoto = work.get("coleta_esgoto_pct", 80).clip(0, 100)
    work["saneamento_risco"] = (100 - regularidade) * 0.65 + (100 - coleta_esgoto) * 0.35
    work["risco_armazenamento_agua"] = (100 - regularidade).clip(0, 100)
    return work


def add_spatial_contagion_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create mobility-weighted contagion pressure from neighboring municipalities."""
    work = df.copy()
    incoming = work.get("fluxo_entrada_pop", 0)
    outgoing = work.get("fluxo_saida_pop", 0)
    neighbor_incidence = work.get("incidencia_vizinhos_ponderada", 0)
    work["mobilidade_fluxo_score"] = np.log1p(incoming + outgoing)
    work["pressao_contagio_espacial"] = neighbor_incidence * (1 + work["mobilidade_fluxo_score"] / 10)
    return work


def add_social_sensor_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create leading indicators from symptom search trends."""
    work = df.copy()
    trend_cols = [
        "google_trends_febre",
        "google_trends_dor_corpo",
        "google_trends_manchas",
        "google_trends_dengue",
    ]
    existing = [col for col in trend_cols if col in work.columns]
    if existing:
        work["social_signal_score"] = work[existing].mean(axis=1).clip(0, 100)
        work["social_signal_delta_2w"] = work.groupby("geocode")["social_signal_score"].diff(2).fillna(0)
    else:
        work["social_signal_score"] = 0
        work["social_signal_delta_2w"] = 0
    return work


def build_orthogonal_feature_block(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all advanced feature blocks in the canonical order."""
    work = add_operational_capacity_features(df)
    work = add_sanitation_features(work)
    work = add_spatial_contagion_features(work)
    work = add_social_sensor_features(work)
    work["resilience_gap_score"] = (
        work["leitos_ocupacao_pct"] * 0.35
        + work["saneamento_risco"] * 0.25
        + work["pressao_contagio_espacial"].clip(0, 100) * 0.25
        + work["social_signal_score"] * 0.15
    ).clip(0, 100)
    return work
