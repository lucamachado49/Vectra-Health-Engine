"""src/data/fetch_mobility.py — Fluxo populacional para modelagem de contágio espacial.

Fontes suportadas:
    1. IBGE Pesquisa de Deslocamento (Censo 2010/2022 — arquivo local).
    2. Fallback: matriz de fluxo gravitacional sintética calibrada por distância e população.

Saída esperada (colunas):
    geocode_origem, geocode_destino, fluxo_diario_estimado

E por município (agregado):
    geocode, fluxo_entrada_pop, fluxo_saida_pop, incidencia_vizinhos_ponderada
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Coordenadas SP (lat, lng, pop_2022)
_SP_CITIES: dict[str, tuple[float, float, int]] = {
    "3550308": (-23.5505, -46.6333, 11_451_245),
    "3509502": (-22.9056, -47.0608,  1_213_792),
    "3518800": (-23.4545, -46.5333,  1_392_121),
    "3543402": (-21.1775, -47.8103,    722_800),
    "3548500": (-23.9608, -46.3336,    433_966),
    "3534401": (-23.5329, -46.7919,    699_283),
    "3513801": (-23.6639, -46.5383,    716_109),
    "3549904": (-23.6939, -46.5650,    833_240),
    "3552205": (-23.5015, -47.4581,    730_006),
    "3506003": (-22.3246, -49.0716,    380_906),
    "3529401": (-23.5231, -46.1874,    457_939),
    "3547304": (-23.1794, -45.8869,    729_737),
    "3541000": (-22.7253, -47.6492,    418_546),
    "3503307": (-22.3572, -47.3830,    148_490),
    "3549805": (-22.0174, -47.8908,    254_484),
}


def fetch_mobility_flows(
    geocodes: list[str],
    ibge_commuting_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Retorna métricas de mobilidade agregadas por município.

    Usa dados IBGE de deslocamento pendular se disponível (CSV local),
    caso contrário aplica modelo gravitacional sintético.

    Args:
        geocodes: Lista de geocodes IBGE de interesse.
        ibge_commuting_path: Caminho para CSV de deslocamento IBGE (opcional).

    Returns:
        DataFrame com fluxo_entrada_pop, fluxo_saida_pop,
        incidencia_vizinhos_ponderada por geocode.
    """
    geocodes = [str(g).zfill(7) for g in geocodes]

    if ibge_commuting_path and Path(ibge_commuting_path).exists():
        try:
            return _load_ibge_commuting(ibge_commuting_path, geocodes)
        except Exception as exc:
            logger.warning("Falha ao carregar IBGE commuting (%s) — usando modelo gravitacional.", exc)

    return _gravitational_model(geocodes)


def _load_ibge_commuting(path: Path, geocodes: list[str]) -> pd.DataFrame:
    raw = pd.read_csv(path, encoding="utf-8", dtype=str)
    raw.columns = raw.columns.str.lower().str.strip()
    raw["fluxo"] = pd.to_numeric(raw.get("pessoas", raw.get("fluxo", 0)), errors="coerce").fillna(0)
    raw["orig"] = raw.get("cod_munic_origem", raw.get("geocode_origem", "")).str.zfill(7)
    raw["dest"] = raw.get("cod_munic_destino", raw.get("geocode_destino", "")).str.zfill(7)

    entrada = raw[raw["dest"].isin(geocodes)].groupby("dest")["fluxo"].sum().rename("fluxo_entrada_pop")
    saida   = raw[raw["orig"].isin(geocodes)].groupby("orig")["fluxo"].sum().rename("fluxo_saida_pop")

    result = pd.DataFrame(index=geocodes)
    result.index.name = "geocode"
    result = result.join(entrada).join(saida).fillna(0).reset_index()
    result["incidencia_vizinhos_ponderada"] = _neighbor_incidence_proxy(result)
    logger.info("IBGE commuting: %d municípios carregados.", len(result))
    return result


def _gravitational_model(geocodes: list[str]) -> pd.DataFrame:
    """Modelo gravitacional: fluxo ~ pop_i * pop_j / distância²."""
    known = {g: _SP_CITIES[g] for g in geocodes if g in _SP_CITIES}
    all_cities = _SP_CITIES

    rows = []
    for geocode in geocodes:
        if geocode not in known:
            rows.append({"geocode": geocode, "fluxo_entrada_pop": 5_000, "fluxo_saida_pop": 5_000})
            continue

        lat1, lng1, pop1 = known[geocode]
        entrada = 0.0
        saida   = 0.0

        for other, (lat2, lng2, pop2) in all_cities.items():
            if other == geocode:
                continue
            dist_km = _haversine(lat1, lng1, lat2, lng2)
            if dist_km < 1:
                dist_km = 1.0
            gravity = (pop1 * pop2) / (dist_km ** 2) * 1e-8
            entrada += gravity
            saida   += gravity * 0.85  # assimetria: capitais atraem mais

        rows.append({
            "geocode":          geocode,
            "fluxo_entrada_pop": round(entrada),
            "fluxo_saida_pop":   round(saida),
        })

    df = pd.DataFrame(rows)
    df["incidencia_vizinhos_ponderada"] = _neighbor_incidence_proxy(df)
    logger.info("Mobilidade: %d municípios via modelo gravitacional.", len(df))
    return df


def _neighbor_incidence_proxy(df: pd.DataFrame) -> pd.Series:
    """Proxy simples: fluxo normalizado como pressão de contágio vizinho."""
    max_flow = df["fluxo_entrada_pop"].max()
    if max_flow == 0:
        return pd.Series(np.zeros(len(df)))
    return (df["fluxo_entrada_pop"] / max_flow * 80).clip(0, 100)


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distância em km entre dois pontos geográficos."""
    r = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lng2 - lng1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))
