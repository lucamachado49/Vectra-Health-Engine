"""src/data/fetch_google_trends.py — Sensores sociais via Google Trends (pytrends).

Busca interesse de pesquisa por sintomas de dengue/arboviroses como
leading indicators epidemiológicos.

Requer:
    pip install pytrends

Fallback sintético ativado automaticamente quando pytrends não está instalado
ou quando a API retorna erro (rate-limit / bloqueio geográfico).

Saída esperada (colunas):
    geocode, semana_iso, google_trends_febre, google_trends_dor_corpo,
    google_trends_manchas, google_trends_dengue
"""
from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

SYMPTOM_KEYWORDS = {
    "google_trends_febre":     "febre dengue",
    "google_trends_dor_corpo": "dor no corpo dengue",
    "google_trends_manchas":   "manchas vermelhas dengue",
    "google_trends_dengue":    "dengue sintomas",
}

# Geo codes do Google Trends para cidades SP
_GTRENDS_GEO = {
    "3550308": "BR-SP-SAO",  # São Paulo
    "3509502": "BR-SP-CAM",  # Campinas
    "3518800": "BR-SP",       # Guarulhos (usa SP-estado)
    "3543402": "BR-SP",
    "3548500": "BR-SP",
}


def fetch_google_trends_symptoms(
    geocodes: list[str],
    start_date: str = "2024-01-01",
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Retorna índices semanais de busca por sintomas de dengue.

    Args:
        geocodes: Lista de geocodes IBGE.
        start_date: Data inicial (YYYY-MM-DD).
        end_date: Data final (YYYY-MM-DD); padrão = hoje.

    Returns:
        DataFrame com índices por semana e keyword.
    """
    if end_date is None:
        end_date = date.today().isoformat()

    geocodes = [str(g).zfill(7) for g in geocodes]

    try:
        from pytrends.request import TrendReq  # noqa: PLC0415
        return _fetch_via_pytrends(geocodes, start_date, end_date)
    except ImportError:
        logger.warning("pytrends não instalado — usando fallback sintético.")
    except Exception as exc:
        logger.warning("Google Trends API falhou (%s) — usando fallback sintético.", exc)

    return _synthetic_fallback(geocodes, start_date, end_date)


def _fetch_via_pytrends(geocodes: list[str], start_date: str, end_date: str) -> pd.DataFrame:
    from pytrends.request import TrendReq  # noqa: PLC0415

    pytrends = TrendReq(hl="pt-BR", tz=-180, timeout=(10, 25))
    timeframe = f"{start_date} {end_date}"
    all_rows: list[dict] = []

    keywords = list(SYMPTOM_KEYWORDS.values())
    geo = "BR-SP"  # Estado de São Paulo como proxy

    pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
    time.sleep(1.5)  # evita rate-limit
    df = pytrends.interest_over_time()

    if df.empty:
        raise ValueError("Google Trends retornou DataFrame vazio.")

    df = df.drop(columns=["isPartial"], errors="ignore")
    df.index = pd.to_datetime(df.index)
    df["semana_iso"] = df.index.isocalendar().week.astype(int)

    col_map = {v: k for k, v in SYMPTOM_KEYWORDS.items()}
    df = df.rename(columns=col_map)

    for geocode in geocodes:
        for _, row in df.iterrows():
            entry: dict = {"geocode": geocode, "semana_iso": int(row["semana_iso"])}
            for col in SYMPTOM_KEYWORDS:
                entry[col] = float(row.get(col, 0))
            all_rows.append(entry)

    logger.info("Google Trends: %d registros coletados.", len(all_rows))
    return pd.DataFrame(all_rows)


def _synthetic_fallback(geocodes: list[str], start_date: str, end_date: str) -> pd.DataFrame:
    """Série temporal sintética com sazonalidade epidemiológica (verão austral = pico)."""
    dates = pd.date_range(start=start_date, end=end_date, freq="W-MON")
    rows: list[dict] = []
    rng = np.random.default_rng(seed=7)

    for geocode in geocodes:
        base_score = {"3550308": 62, "3509502": 54, "3518800": 51}.get(geocode, 45)
        for dt in dates:
            month = dt.month
            # Pico verão/outono austral (jan–abr) onde dengue é endêmica no Brasil
            seasonal_boost = 30 if month in (1, 2, 3, 4) else (10 if month in (11, 12) else 0)
            noise = rng.normal(0, 6, 4)
            rows.append({
                "geocode":                  geocode,
                "semana_iso":               int(dt.isocalendar()[1]),
                "google_trends_febre":      float(np.clip(base_score + seasonal_boost + noise[0], 0, 100)),
                "google_trends_dor_corpo":  float(np.clip(base_score - 5 + seasonal_boost + noise[1], 0, 100)),
                "google_trends_manchas":    float(np.clip(base_score - 10 + seasonal_boost + noise[2], 0, 100)),
                "google_trends_dengue":     float(np.clip(base_score + seasonal_boost * 1.2 + noise[3], 0, 100)),
            })

    logger.info("Google Trends: %d registros via fallback sintético.", len(rows))
    return pd.DataFrame(rows)
