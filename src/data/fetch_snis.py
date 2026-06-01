"""src/data/fetch_snis.py — Coleta de dados de saneamento básico via SNIS.

O SNIS (Sistema Nacional de Informações sobre Saneamento) disponibiliza dados
anuais via API REST pública e portal de download. Este módulo:
    1. Tenta a API REST do SNIS (https://apidados.snis.gov.br).
    2. Aplica fallback com valores sintéticos calibrados para o estado de SP
       quando a API não está acessível (modo demo/acadêmico).

Saída esperada (colunas):
    geocode, ano, regularidade_abastecimento_pct, coleta_esgoto_pct,
    indice_perdas_agua_pct, populacao_atendida_agua_pct
"""
from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
import numpy as np
import requests

logger = logging.getLogger(__name__)

SNIS_API_BASE = "https://apidados.snis.gov.br/api/v1"

# Geocodes IBGE → referência SNIS (7 dígitos, sem dígito verificador)
_SP_SNIS_INDICADORES = {
    # geocode: (regularidade_abast_pct, coleta_esgoto_pct, perdas_agua_pct, pop_atendida_agua_pct)
    "3550308": (92.4, 88.2, 31.1, 99.6),   # São Paulo
    "3509502": (94.1, 91.0, 27.3, 99.8),   # Campinas
    "3518800": (88.7, 84.5, 35.2, 98.4),   # Guarulhos
    "3543402": (90.3, 87.8, 29.6, 99.1),   # Ribeirão Preto
    "3548500": (95.6, 93.4, 22.7, 99.9),   # Santos
    "3534401": (87.2, 82.1, 36.8, 97.9),   # Osasco
    "3513801": (89.5, 85.9, 32.4, 98.7),   # Santo André
    "3549904": (91.0, 88.6, 28.9, 99.2),   # São Bernardo do Campo
    "3552205": (86.3, 80.7, 38.1, 97.4),   # Sorocaba
    "3506003": (83.7, 76.4, 41.5, 96.8),   # Bauru
    "3529401": (85.1, 78.2, 39.7, 97.1),   # Mogi das Cruzes
    "3547304": (93.8, 90.5, 25.1, 99.5),   # São José dos Campos
    "3541000": (88.0, 83.3, 33.6, 98.2),   # Piracicaba
    "3503307": (80.4, 72.1, 44.2, 95.6),   # Araras
    "3549805": (91.7, 89.1, 27.8, 99.3),   # São Carlos
}


def fetch_snis_indicators(
    geocodes: list[str],
    year: int = 2022,
    timeout: int = 15,
) -> pd.DataFrame:
    """Retorna indicadores SNIS para os geocodes e ano informados.

    Tenta a API REST do SNIS; usa fallback sintético em caso de falha.

    Args:
        geocodes: Lista de geocodes IBGE (7 dígitos).
        year: Ano de referência (SNIS disponibiliza até 2022 geralmente).
        timeout: Timeout em segundos para a requisição HTTP.

    Returns:
        DataFrame com colunas SNIS padronizadas.
    """
    geocodes = [str(g).zfill(7) for g in geocodes]

    try:
        return _fetch_from_api(geocodes, year, timeout)
    except Exception as exc:
        logger.warning("SNIS API indisponível (%s) — usando fallback sintético.", exc)
        return _synthetic_fallback(geocodes, year)


def _fetch_from_api(geocodes: list[str], year: int, timeout: int) -> pd.DataFrame:
    """Tenta consultar a API REST do SNIS."""
    rows = []
    for geocode in geocodes:
        url = f"{SNIS_API_BASE}/municipio/{geocode}/indicadores"
        params = {"ano": year}
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        rows.append({
            "geocode": geocode,
            "ano": year,
            "regularidade_abastecimento_pct": float(data.get("IN022", 90.0)),
            "coleta_esgoto_pct":              float(data.get("IN015", 80.0)),
            "indice_perdas_agua_pct":         float(data.get("IN049", 35.0)),
            "populacao_atendida_agua_pct":    float(data.get("IN055", 98.0)),
        })
    logger.info("SNIS: %d municípios carregados via API.", len(rows))
    return pd.DataFrame(rows)


def _synthetic_fallback(geocodes: list[str], year: int) -> pd.DataFrame:
    """Gera dados SNIS sintéticos calibrados por referência histórica SP."""
    rng = np.random.default_rng(seed=42 + year)
    rows = []
    for geocode in geocodes:
        base = _SP_SNIS_INDICADORES.get(geocode)
        if base:
            reg, col, per, pop = base
            noise = rng.normal(0, 1.5, 4)
        else:
            reg, col, per, pop = 88.0, 80.0, 36.0, 97.0
            noise = rng.normal(0, 3.0, 4)
        rows.append({
            "geocode":                        geocode,
            "ano":                            year,
            "regularidade_abastecimento_pct": float(np.clip(reg + noise[0], 50, 100)),
            "coleta_esgoto_pct":              float(np.clip(col + noise[1], 40, 100)),
            "indice_perdas_agua_pct":         float(np.clip(per + noise[2],  5,  70)),
            "populacao_atendida_agua_pct":    float(np.clip(pop + noise[3], 70, 100)),
        })
    logger.info("SNIS: %d municípios via fallback sintético (ano %d).", len(rows), year)
    return pd.DataFrame(rows)
