"""
src/data/fetch_ibge.py — Coleta de dados populacionais via IBGE SIDRA.

Tabela SIDRA 6579: Estimativas populacionais municipais.
"""
from __future__ import annotations

import logging

import pandas as pd
import requests

from src.config import IBGE_SIDRA_BASE_URL

logger = logging.getLogger(__name__)


def fetch_ibge_population_sidra(year: int = 2021) -> pd.DataFrame:
    """
    Coleta população municipal estimada via API SIDRA.

    Args:
        year: Ano da estimativa populacional.

    Returns:
        DataFrame com população municipal.
    """
    url = f"{IBGE_SIDRA_BASE_URL}/t/6579/n6/all/v/9324/p/{year}"
    logger.info("IBGE SIDRA: ano=%s", year)
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    payload = response.json()
    if len(payload) <= 1:
        raise ValueError("Resposta IBGE/SIDRA vazia.")
    df = pd.DataFrame(payload[1:])
    rename_map = {"D1C": "geocode", "D1N": "municipio", "D2C": "ano", "V": "populacao"}
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    if "populacao" in df.columns:
        df["populacao"] = pd.to_numeric(df["populacao"], errors="coerce")
    if "geocode" in df.columns:
        df["geocode"] = df["geocode"].astype(str)
    logger.info("IBGE população coletada | ano=%s | shape=%s", year, df.shape)
    return df
