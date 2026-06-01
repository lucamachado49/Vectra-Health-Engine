"""src/data/fetch_satellite_cv.py — Visão Computacional por satélite (NDVI/NDWI).

Extrai índices espectrais reais de imagens Sentinel-2 / MODIS via Google Earth
Engine (GEE) para cada município, gerando as máscaras de visão computacional
usadas no risco ambiental:

    NDVI  — vegetação (Normalized Difference Vegetation Index)
    NDWI  — água superficial / umidade (Normalized Difference Water Index)
    LST   — temperatura de superfície (ilhas de calor)

⚠️ REQUER CREDENCIAIS: Google Earth Engine exige autenticação. Defina:
       VECTRA_GEE_SERVICE_ACCOUNT=<email-da-conta-de-servico>
       VECTRA_GEE_KEY_FILE=<caminho-para-a-chave-json>
   ou rode `earthengine authenticate` previamente.

   Instale: pip install earthengine-api

Sem credenciais/biblioteca, o módulo usa fallback sintético determinístico
(calibrado por bioma/região) para manter o pipeline executável.

Uso:
    python -m src.data.fetch_satellite_cv --ufs SP,BA --start 2025-01-01 --end 2025-05-14

Saída:
    data/raw/satellite/cv_indices_municipios.csv
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()                                   # .env na raiz
    load_dotenv(Path("api/.env"))                   # .env da API
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

GEOCODES_FILE = Path("frontend/public/geo/risk-national.json")
OUTPUT_FILE = Path("data/raw/satellite/cv_indices_municipios.csv")

# bioma aproximado por região → calibra NDVI/NDWI base
REGION_SPECTRAL = {
    "Norte":        {"ndvi": 0.78, "ndwi": 0.55, "lst": 31},   # Amazônia: vegetação densa, muita água
    "Nordeste":     {"ndvi": 0.42, "ndwi": 0.30, "lst": 34},   # Caatinga/litoral: seco e quente
    "Centro-Oeste": {"ndvi": 0.60, "ndwi": 0.28, "lst": 33},   # Cerrado/Pantanal
    "Sudeste":      {"ndvi": 0.55, "ndwi": 0.32, "lst": 30},   # Mata Atlântica/urbano
    "Sul":          {"ndvi": 0.62, "ndwi": 0.35, "lst": 24},   # subtropical
}


# ----------------------------------------------------------------------
# Google Earth Engine (caminho real)
# ----------------------------------------------------------------------

def _init_gee() -> bool:
    """Inicializa o Earth Engine se a lib e as credenciais existirem."""
    try:
        import ee  # noqa: PLC0415
    except ImportError:
        logger.warning("earthengine-api não instalado. Use: pip install earthengine-api")
        return False

    service_account = os.getenv("VECTRA_GEE_SERVICE_ACCOUNT")
    key_file = os.getenv("VECTRA_GEE_KEY_FILE")

    try:
        if service_account and key_file and Path(key_file).exists():
            credentials = ee.ServiceAccountCredentials(service_account, key_file)
            ee.Initialize(credentials)
            logger.info("GEE inicializado via conta de serviço.")
        else:
            ee.Initialize()  # usa credenciais do `earthengine authenticate`
            logger.info("GEE inicializado via credenciais locais.")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao inicializar GEE (%s). Usando fallback sintético.", exc)
        return False


def _compute_indices_gee(lat: float, lng: float, start: str, end: str, buffer_m: int = 5000) -> dict | None:
    """Calcula NDVI/NDWI/LST médios numa área ao redor do ponto via Sentinel-2 + MODIS."""
    try:
        import ee  # noqa: PLC0415

        point = ee.Geometry.Point([lng, lat])
        region = point.buffer(buffer_m)

        # Sentinel-2 SR, com máscara de nuvens
        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
            .median()
        )
        ndvi = s2.normalizedDifference(["B8", "B4"]).rename("NDVI")
        ndwi = s2.normalizedDifference(["B3", "B8"]).rename("NDWI")

        # MODIS LST (temperatura de superfície, Kelvin*0.02 → °C)
        lst = (
            ee.ImageCollection("MODIS/061/MOD11A1")
            .filterBounds(region)
            .filterDate(start, end)
            .select("LST_Day_1km")
            .mean()
            .multiply(0.02)
            .subtract(273.15)
            .rename("LST")
        )

        stack = ndvi.addBands(ndwi).addBands(lst)
        stats = stack.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=region, scale=100, maxPixels=1e9,
        ).getInfo()

        return {
            "ndvi_mean": stats.get("NDVI"),
            "ndwi_mean": stats.get("NDWI"),
            "lst_mean": stats.get("LST"),
        }
    except Exception as exc:  # noqa: BLE001
        logger.debug("GEE falhou no ponto (%s,%s): %s", lat, lng, exc)
        return None


# ----------------------------------------------------------------------
# Fallback sintético
# ----------------------------------------------------------------------

def _synthetic_indices(geocode: str, region: str) -> dict:
    """Índices espectrais sintéticos determinísticos por bioma/região."""
    base = REGION_SPECTRAL.get(region, REGION_SPECTRAL["Sudeste"])
    h = int(hashlib.md5(geocode.encode()).hexdigest(), 16)
    j = (h % 1000) / 1000.0 * 2 - 1  # -1..1
    ndvi = float(np.clip(base["ndvi"] + j * 0.18, 0.05, 0.95))
    ndwi = float(np.clip(base["ndwi"] + j * 0.15, -0.10, 0.85))
    lst = float(np.clip(base["lst"] + j * 4, 14, 44))
    # ilha de calor: LST relativa normalizada 0-100
    heat = float(np.clip((lst - 18) / 26 * 100, 0, 100))
    return {"ndvi_mean": round(ndvi, 3), "ndwi_mean": round(ndwi, 3),
            "lst_mean": round(lst, 1), "heat_island_score": round(heat, 1)}


# ----------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------

def run(
    start: str, end: str, ufs: list[str] | None = None, limit: int | None = None,
) -> None:
    """Gera índices CV por município (GEE real ou fallback sintético)."""
    if not GEOCODES_FILE.exists():
        raise FileNotFoundError(
            f"{GEOCODES_FILE} não existe. Rode: python scripts/build_geo_assets.py"
        )

    geo = json.loads(GEOCODES_FILE.read_text(encoding="utf-8"))
    if ufs:
        geo = {g: v for g, v in geo.items() if v.get("uf") in ufs}
    items = list(geo.items())
    if limit:
        items = items[:limit]

    gee_ready = _init_gee()
    mode = "GEE-REAL" if gee_ready else "SINTÉTICO"
    logger.info("CV satélite | modo=%s | municípios=%d | janela=%s..%s", mode, len(items), start, end)

    # coordenadas só existem para os municípios curados;
    # para os demais, o fallback sintético independe de coordenadas.
    try:
        from src.data._coords import MUNI_COORDS  # noqa: PLC0415
    except ImportError:
        MUNI_COORDS = {}

    rows = []
    for i, (geocode, meta) in enumerate(items, 1):
        region = meta.get("r", "Sudeste")
        result = None
        if gee_ready:
            coords = MUNI_COORDS.get(geocode) if MUNI_COORDS else None
            if coords:
                result = _compute_indices_gee(coords[0], coords[1], start, end)
                if result:
                    # deriva heat score
                    lst = result.get("lst_mean") or 28
                    result["heat_island_score"] = round(float(np.clip((lst - 18) / 26 * 100, 0, 100)), 1)
        if not result:
            result = _synthetic_indices(geocode, region)

        rows.append({"geocode": geocode, "uf": meta.get("uf"), "region": region, **result})
        if i % 200 == 0:
            logger.info("CV: %d/%d municípios", i, len(items))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    logger.info("CV índices salvos: %s | %d municípios | modo=%s", OUTPUT_FILE, len(rows), mode)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--end", default="2025-05-14")
    parser.add_argument("--ufs", default=None, help="UFs separadas por vírgula.")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    ufs = [u.strip().upper() for u in args.ufs.split(",")] if args.ufs else None
    run(start=args.start, end=args.end, ufs=ufs, limit=args.limit)


if __name__ == "__main__":
    main()
