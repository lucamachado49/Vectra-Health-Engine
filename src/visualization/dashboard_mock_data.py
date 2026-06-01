"""Fallback dashboard data used when the API has no processed artifacts yet."""
from __future__ import annotations

DEMO_LATEST_RISK = [
    {
        "geocode": "3550308",
        "municipio": "Sao Paulo",
        "ano": 2025,
        "semana_epidemiologica": 12,
        "casos_dengue": 245,
        "incidencia_100k": 32.4,
        "environmental_risk_score": 84,
        "risco_ambiental_label": "alto",
        "temp_media_7d": 27.8,
        "chuva_acumulada_7d": 64.2,
        "umidade_media_7d": 81.5,
    },
    {
        "geocode": "3509502",
        "municipio": "Campinas",
        "ano": 2025,
        "semana_epidemiologica": 12,
        "casos_dengue": 171,
        "incidencia_100k": 29.1,
        "environmental_risk_score": 72,
        "risco_ambiental_label": "alto",
        "temp_media_7d": 28.2,
        "chuva_acumulada_7d": 51.8,
        "umidade_media_7d": 78.3,
    },
]

__all__ = ["DEMO_LATEST_RISK"]
