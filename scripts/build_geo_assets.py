"""scripts/build_geo_assets.py — Gera assets geoespaciais do Vectra Health.

Baixa GeoJSON público (estados + municípios por UF), simplifica as coordenadas
para reduzir o tamanho, e gera uma base de risco nacional sintética calibrada
por região e sazonalidade. Saída em frontend/public/geo/.

Uso:
    python scripts/build_geo_assets.py
    python scripts/build_geo_assets.py --ufs SP,BA,CE   # apenas alguns estados

Saídas:
    frontend/public/geo/brazil-states.json   — polígonos dos 27 estados
    frontend/public/geo/mun/{UF}.json        — municípios simplificados por estado
    frontend/public/geo/risk-national.json   — score de risco por geocode (sintético)
    frontend/public/geo/manifest.json        — índice de arquivos disponíveis
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

OUT_DIR = Path("frontend/public/geo")
MUN_DIR = OUT_DIR / "mun"

STATES_URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
MUN_URL = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-{code}-mun.json"

# UF sigla -> (código IBGE, região)
UF_INFO: dict[str, tuple[str, str]] = {
    "RO": ("11", "Norte"),        "AC": ("12", "Norte"),        "AM": ("13", "Norte"),
    "RR": ("14", "Norte"),        "PA": ("15", "Norte"),        "AP": ("16", "Norte"),
    "TO": ("17", "Norte"),        "MA": ("21", "Nordeste"),     "PI": ("22", "Nordeste"),
    "CE": ("23", "Nordeste"),     "RN": ("24", "Nordeste"),     "PB": ("25", "Nordeste"),
    "PE": ("26", "Nordeste"),     "AL": ("27", "Nordeste"),     "SE": ("28", "Nordeste"),
    "BA": ("29", "Nordeste"),     "MG": ("31", "Sudeste"),      "ES": ("32", "Sudeste"),
    "RJ": ("33", "Sudeste"),      "SP": ("35", "Sudeste"),      "PR": ("41", "Sul"),
    "SC": ("42", "Sul"),          "RS": ("43", "Sul"),          "MS": ("50", "Centro-Oeste"),
    "MT": ("51", "Centro-Oeste"), "GO": ("52", "Centro-Oeste"), "DF": ("53", "Centro-Oeste"),
}

# Risco-base por região (média) + amplitude. Calibrado por endemicidade de arboviroses.
REGION_RISK = {
    "Norte":        (78, 22),
    "Nordeste":     (74, 26),
    "Centro-Oeste": (68, 24),
    "Sudeste":      (62, 30),
    "Sul":          (40, 26),
}

PRECISION = 3  # casas decimais (~110m) — bom equilíbrio tamanho/qualidade


# ----------------------------------------------------------------------
# Simplificação de coordenadas (pure-python, sem geopandas)
# ----------------------------------------------------------------------

def _round_ring(ring: list) -> list:
    """Arredonda e remove pontos consecutivos duplicados de um anel."""
    out = []
    last = None
    for pt in ring:
        rp = [round(pt[0], PRECISION), round(pt[1], PRECISION)]
        if rp != last:
            out.append(rp)
            last = rp
    # garante anel fechado e mínimo de 4 pontos
    if len(out) >= 1 and out[0] != out[-1]:
        out.append(out[0])
    return out if len(out) >= 4 else ring


def _simplify_geometry(geom: dict) -> dict:
    """Simplifica geometria Polygon/MultiPolygon arredondando coordenadas."""
    t = geom.get("type")
    c = geom.get("coordinates")
    if t == "Polygon":
        geom["coordinates"] = [_round_ring(r) for r in c]
    elif t == "MultiPolygon":
        geom["coordinates"] = [[_round_ring(r) for r in poly] for poly in c]
    return geom


# ----------------------------------------------------------------------
# Risco sintético determinístico
# ----------------------------------------------------------------------

def _synthetic_risk(geocode: str, region: str) -> dict:
    """Gera score de risco determinístico a partir do geocode + região."""
    base, spread = REGION_RISK.get(region, (60, 25))
    h = int(hashlib.md5(geocode.encode()).hexdigest(), 16)
    # distribui no intervalo [base-spread, base+spread]
    offset = (h % 1000) / 1000.0 * 2 - 1  # -1..1
    score = base + offset * spread
    score = max(8, min(99, round(score, 1)))

    casos = int((h % 400) * (score / 100) ** 1.5)
    incid = round((h % 60) * (score / 100), 1)
    return {
        "s": score,                                   # environmental_risk_score
        "c": casos,                                   # casos_dengue
        "i": incid,                                   # incidencia_100k
    }


# ----------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------

def build_states() -> None:
    logger.info("Baixando estados...")
    r = requests.get(STATES_URL, timeout=90)
    r.raise_for_status()
    data = r.json()
    for f in data["features"]:
        f["geometry"] = _simplify_geometry(f["geometry"])
        # normaliza propriedades
        props = f["properties"]
        f["properties"] = {"sigla": props.get("sigla"), "name": props.get("name")}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "brazil-states.json"
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    logger.info("Estados salvos: %s (%.2f MB)", path, path.stat().st_size / 1e6)


def build_municipalities(ufs: list[str]) -> dict:
    MUN_DIR.mkdir(parents=True, exist_ok=True)
    national_risk: dict[str, dict] = {}
    manifest_ufs: list[str] = []

    for uf in ufs:
        code, region = UF_INFO[uf]
        try:
            logger.info("Baixando municípios de %s (cod %s)...", uf, code)
            r = requests.get(MUN_URL.format(code=code), timeout=90)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha em %s: %s", uf, exc)
            continue

        for f in data["features"]:
            props = f["properties"]
            geocode = str(props.get("id", ""))
            name = props.get("name", "")
            f["geometry"] = _simplify_geometry(f["geometry"])
            risk = _synthetic_risk(geocode, region)
            f["properties"] = {
                "geocode": geocode,
                "name": name,
                "uf": uf,
                "region": region,
                "score": risk["s"],
            }
            national_risk[geocode] = {**risk, "uf": uf, "n": name, "r": region}

        path = MUN_DIR / f"{uf}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        manifest_ufs.append(uf)
        logger.info("  %s: %d municípios | %.2f MB", uf, len(data["features"]), path.stat().st_size / 1e6)

    # risco nacional consolidado
    risk_path = OUT_DIR / "risk-national.json"
    risk_path.write_text(json.dumps(national_risk, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    logger.info("Risco nacional: %d municípios | %.2f MB", len(national_risk), risk_path.stat().st_size / 1e6)

    return {"ufs": manifest_ufs, "municipalities": len(national_risk)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ufs", default="ALL", help="Lista de UFs separadas por vírgula, ou ALL")
    args = parser.parse_args()

    ufs = list(UF_INFO.keys()) if args.ufs == "ALL" else [u.strip().upper() for u in args.ufs.split(",")]

    build_states()
    summary = build_municipalities(ufs)

    manifest = {
        "generated": True,
        "states_file": "brazil-states.json",
        "risk_file": "risk-national.json",
        "ufs": summary["ufs"],
        "total_municipalities": summary["municipalities"],
        "region_by_uf": {uf: info[1] for uf, info in UF_INFO.items()},
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    logger.info("Manifest salvo. UFs processadas: %d | municípios: %d",
                len(summary["ufs"]), summary["municipalities"])


if __name__ == "__main__":
    main()
