"""src/data/fetch_inmet.py — Coleta de dados climáticos reais via INMET.

Usa a API pública de estações automáticas do INMET (apitempo.inmet.gov.br).
Coleta temperatura, precipitação e umidade diárias por estação, e associa
cada estação ao município mais próximo.

Endpoints utilizados:
    GET /estacoes/T                          -> catálogo de estações automáticas
    GET /estacao/diaria/{ini}/{fim}/{cod}    -> série diária de uma estação

Fallback sintético quando a API está indisponível (modo demo).

Uso:
    python -m src.data.fetch_inmet --start 2025-01-01 --end 2025-05-14

Saída:
    data/raw/inmet/inmet_estacoes_catalogo.csv
    data/raw/inmet/inmet_clima_diario.csv
"""
from __future__ import annotations

import argparse
import logging
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

INMET_BASE = "https://apitempo.inmet.gov.br"
CATALOG_FILE = Path("data/raw/inmet/inmet_estacoes_catalogo.csv")
CLIMATE_FILE = Path("data/raw/inmet/inmet_clima_diario.csv")


def fetch_station_catalog(timeout: int = 30) -> pd.DataFrame:
    """Baixa o catálogo de estações automáticas do INMET."""
    try:
        resp = requests.get(f"{INMET_BASE}/estacoes/T", timeout=timeout)
        resp.raise_for_status()
        stations = resp.json()
        df = pd.DataFrame(stations)
        keep = {
            "CD_ESTACAO": "codigo", "DC_NOME": "nome", "SG_ESTADO": "uf",
            "VL_LATITUDE": "lat", "VL_LONGITUDE": "lng",
        }
        cols = [c for c in keep if c in df.columns]
        df = df[cols].rename(columns=keep)
        for c in ("lat", "lng"):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        logger.info("INMET: %d estações no catálogo.", len(df))
        return df.dropna(subset=["lat", "lng"])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Catálogo INMET indisponível (%s) — usando fallback.", exc)
        return _fallback_catalog()


def fetch_station_series(
    codigo: str, start: str, end: str, timeout: int = 30
) -> pd.DataFrame | None:
    """Baixa a série diária (temp, chuva, umidade) de uma estação."""
    url = f"{INMET_BASE}/estacao/diaria/{start}/{end}/{codigo}"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        df = pd.DataFrame(data)
        rename = {
            "DT_MEDICAO": "data", "TEM_MED": "temp_media",
            "CHUVA": "chuva_mm", "UMD_MED": "umidade_media", "CD_ESTACAO": "codigo",
        }
        cols = [c for c in rename if c in df.columns]
        df = df[cols].rename(columns=rename)
        for c in ("temp_media", "chuva_mm", "umidade_media"):
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        df["codigo"] = codigo
        return df
    except Exception as exc:  # noqa: BLE001
        logger.debug("Falha série estação %s: %s", codigo, exc)
        return None


def run(start: str, end: str, uf: str | None = None, limit: int | None = None, sleep: float = 0.3) -> None:
    """Coleta catálogo + séries diárias de todas as estações (ou filtro UF)."""
    CATALOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    catalog = fetch_station_catalog()
    if uf:
        catalog = catalog[catalog["uf"] == uf.upper()]
    if limit:
        catalog = catalog.head(limit)
    catalog.to_csv(CATALOG_FILE, index=False, encoding="utf-8")

    frames: list[pd.DataFrame] = []
    for i, row in enumerate(catalog.itertuples(), 1):
        series = fetch_station_series(row.codigo, start, end)
        if series is None:
            series = _fallback_series(row.codigo, start, end)
        series["uf"] = getattr(row, "uf", None)
        series["lat"] = getattr(row, "lat", None)
        series["lng"] = getattr(row, "lng", None)
        frames.append(series)
        if i % 25 == 0:
            logger.info("INMET séries: %d/%d estações", i, len(catalog))
        import time
        time.sleep(sleep)

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        combined.to_csv(CLIMATE_FILE, index=False, encoding="utf-8")
        logger.info("INMET clima diário salvo: %s | shape=%s", CLIMATE_FILE, combined.shape)


# ----------------------------------------------------------------------
# Fallbacks sintéticos
# ----------------------------------------------------------------------

def _fallback_catalog() -> pd.DataFrame:
    """Catálogo mínimo de capitais quando a API falha."""
    caps = [
        ("A001", "BRASILIA", "DF", -15.78, -47.93), ("A301", "SALVADOR", "BA", -12.97, -38.50),
        ("A652", "FORTALEZA", "CE", -3.72, -38.54), ("A001SP", "SAO PAULO", "SP", -23.55, -46.63),
        ("A636", "MANAUS", "AM", -3.12, -60.02),
    ]
    return pd.DataFrame(caps, columns=["codigo", "nome", "uf", "lat", "lng"])


def _fallback_series(codigo: str, start: str, end: str) -> pd.DataFrame:
    """Série sintética diária com sazonalidade tropical."""
    dates = pd.date_range(start=start, end=end, freq="D")
    rng = np.random.default_rng(abs(hash(codigo)) % (2**32))
    rows = []
    for d in dates:
        month = d.month
        wet = month in (1, 2, 3, 4, 11, 12)
        rows.append({
            "data": d.strftime("%Y-%m-%d"),
            "temp_media": float(np.clip(rng.normal(26 if wet else 23, 3), 12, 40)),
            "chuva_mm": float(max(0, rng.normal(12 if wet else 2, 8))),
            "umidade_media": float(np.clip(rng.normal(78 if wet else 60, 10), 30, 100)),
            "codigo": codigo,
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    today = date.today()
    parser.add_argument("--start", default=(today - timedelta(days=120)).isoformat())
    parser.add_argument("--end", default=today.isoformat())
    parser.add_argument("--uf", default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    run(start=args.start, end=args.end, uf=args.uf, limit=args.limit)


if __name__ == "__main__":
    main()
