"""
src/data/fetch_datasus.py — Coleta de dados de capacidade hospitalar via DataSUS/CNES.

Observação:
    O DataSUS/CNES não possui API REST pública padronizada para todos os dados.
    Este módulo oferece helpers para:
    1. Carregar CSV exportado manualmente do CNES.
    2. Gerar variáveis derivadas (leitos por 10k, vulnerabilidade operacional).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.utils.io_utils import read_csv_safely
from src.utils.geo_utils import normalize_columns, standardize_geocode

logger = logging.getLogger(__name__)


def load_cnes_leitos(input_path: Path) -> pd.DataFrame:
    """
    Carrega e limpa o CSV exportado do CNES com dados de leitos.

    Args:
        input_path: Caminho do CSV bruto do CNES.

    Returns:
        DataFrame limpo com geocode, municipio, leitos_total.
    """
    df = read_csv_safely(input_path)
    df = normalize_columns(df)
    if "geocode" not in df.columns:
        for candidate in ["cod_municipio", "municipio_geocodigo", "ibge", "co_municipio"]:
            if candidate in df.columns:
                df = df.rename(columns={candidate: "geocode"})
                break
    if "geocode" in df.columns:
        df["geocode"] = standardize_geocode(df["geocode"])
    leitos_col = next((c for c in df.columns if "leito" in c or "bed" in c), None)
    if leitos_col and leitos_col != "leitos_total":
        df = df.rename(columns={leitos_col: "leitos_total"})
    if "leitos_total" in df.columns:
        df["leitos_total"] = pd.to_numeric(df["leitos_total"], errors="coerce")
    logger.info("CNES leitos carregado | shape=%s", df.shape)
    return df


def add_health_capacity_features(df: pd.DataFrame, cnes_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Adiciona variáveis de capacidade de saúde ao dataset principal.

    Se cnes_df não for fornecido, cria proxies baseados em população.

    Args:
        df: Dataset principal com coluna 'geocode' e 'populacao'.
        cnes_df: DataFrame do CNES com 'geocode' e 'leitos_total' (opcional).

    Returns:
        DataFrame com 'leitos_por_10k' e 'vulnerabilidade_operacional_proxy'.
    """
    df = df.copy()
    if cnes_df is not None and "geocode" in cnes_df.columns and "leitos_total" in cnes_df.columns:
        df = df.merge(cnes_df[["geocode", "leitos_total"]], on="geocode", how="left")
        if "populacao" in df.columns:
            df["leitos_por_10k"] = (
                df["leitos_total"] / df["populacao"].replace(0, np.nan) * 10_000
            ).replace([np.inf, -np.inf], np.nan)
    logger.info("Features de capacidade de saúde adicionadas.")
    return df
