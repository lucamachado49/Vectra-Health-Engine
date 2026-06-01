"""
src/data/fetch_infodengue.py — Coleta de dados epidemiológicos via InfoDengue.

Fonte: https://info.dengue.mat.br/api/alertcity

Funções:
    fetch_infodengue_alertcity  — Coleta para um município.
    fetch_infodengue_for_many_cities — Coleta para múltiplos municípios.
"""
from __future__ import annotations

import logging
from io import StringIO
from typing import Iterable

import pandas as pd
import requests

from src.config import INFODENGUE_BASE_URL

logger = logging.getLogger(__name__)


def safe_get(url: str, timeout: int = 60) -> requests.Response:
    """Executa GET com tratamento de erro."""
    logger.info("Requisição: %s", url)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response


def fetch_infodengue_alertcity(
    geocode: int | str,
    disease: str = "dengue",
    ey_start: int = 2020,
    ey_end: int = 2025,
    ew_start: int = 1,
    ew_end: int = 53,
) -> pd.DataFrame:
    """
    Coleta dados semanais do InfoDengue para um município.

    Args:
        geocode: Código IBGE do município.
        disease: Doença monitorada (dengue, zika, chikungunya).
        ey_start: Ano epidemiológico inicial.
        ey_end: Ano epidemiológico final.
        ew_start: Semana epidemiológica inicial.
        ew_end: Semana epidemiológica final.

    Returns:
        DataFrame com os dados retornados pela API.
    """
    url = (
        f"{INFODENGUE_BASE_URL}?geocode={geocode}"
        f"&disease={disease}&format=csv"
        f"&ew_start={ew_start}&ew_end={ew_end}"
        f"&ey_start={ey_start}&ey_end={ey_end}"
    )
    response = safe_get(url)
    df = pd.read_csv(StringIO(response.text))
    df["geocode"] = str(geocode)
    df["disease"] = disease
    logger.info("InfoDengue coletado | geocode=%s | doença=%s | shape=%s", geocode, disease, df.shape)
    return df


def fetch_infodengue_for_many_cities(
    geocodes: Iterable[int | str],
    disease: str = "dengue",
    ey_start: int = 2020,
    ey_end: int = 2025,
) -> pd.DataFrame:
    """Coleta InfoDengue para múltiplos municípios e concatena."""
    frames: list[pd.DataFrame] = []
    for geocode in geocodes:
        try:
            frames.append(fetch_infodengue_alertcity(geocode=geocode, disease=disease, ey_start=ey_start, ey_end=ey_end))
        except Exception as exc:
            logger.warning("Falha ao coletar InfoDengue | geocode=%s | erro=%s", geocode, exc)
    if not frames:
        raise ValueError("Nenhum dado do InfoDengue foi coletado.")
    df = pd.concat(frames, ignore_index=True)
    logger.info("InfoDengue consolidado | shape=%s", df.shape)
    return df
