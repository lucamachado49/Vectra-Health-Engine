"""
src/data/fetch_nasa_power.py — Coleta de dados climáticos via NASA POWER API.

Fonte: https://power.larc.nasa.gov/api/temporal/daily/point

Variáveis padrão coletadas:
    T2M       — Temperatura média 2m
    T2M_MAX   — Temperatura máxima
    T2M_MIN   — Temperatura mínima
    RH2M      — Umidade relativa
    PRECTOTCORR — Precipitação corrigida
"""
from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
import requests

from src.config import NASA_POWER_BASE_URL

logger = logging.getLogger(__name__)

DEFAULT_PARAMETERS = ["T2M", "T2M_MAX", "T2M_MIN", "RH2M", "PRECTOTCORR"]


def fetch_nasa_power_daily_point(
    latitude: float,
    longitude: float,
    start: str,
    end: str,
    parameters: Optional[list[str]] = None,
    community: str = "AG",
) -> dict:
    """
    Coleta dados diários da NASA POWER API para uma coordenada.

    Args:
        latitude: Latitude do ponto de interesse.
        longitude: Longitude do ponto de interesse.
        start: Data inicial no formato YYYYMMDD.
        end: Data final no formato YYYYMMDD.
        parameters: Lista de variáveis NASA POWER. Usa DEFAULT_PARAMETERS se None.
        community: Comunidade da API (AG para clima/agro).

    Returns:
        Payload JSON retornado pela NASA POWER.
    """
    if parameters is None:
        parameters = DEFAULT_PARAMETERS
    url = (
        f"{NASA_POWER_BASE_URL}?parameters={','.join(parameters)}"
        f"&community={community}&longitude={longitude}&latitude={latitude}"
        f"&start={start}&end={end}&format=JSON"
    )
    logger.info("NASA POWER: lat=%s lon=%s start=%s end=%s", latitude, longitude, start, end)
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    return response.json()


def nasa_power_json_to_dataframe(payload: dict, geocode: int | str, municipio: str) -> pd.DataFrame:
    """
    Converte o JSON da NASA POWER em DataFrame tabular.

    Args:
        payload: JSON retornado pela NASA POWER API.
        geocode: Código IBGE do município relacionado.
        municipio: Nome do município.

    Returns:
        DataFrame diário com variáveis climáticas.
    """
    parameters = payload.get("properties", {}).get("parameter", {})
    if not parameters:
        raise ValueError("Payload NASA POWER não contém properties.parameter.")
    frames = []
    for var_name, values_by_date in parameters.items():
        frames.append(pd.DataFrame({"date": list(values_by_date.keys()), var_name: list(values_by_date.values())}))
    df = frames[0]
    for frame in frames[1:]:
        df = df.merge(frame, on="date", how="outer")
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d", errors="coerce")
    df["geocode"] = str(geocode)
    df["municipio"] = municipio
    logger.info("NASA POWER convertido | shape=%s", df.shape)
    return df
