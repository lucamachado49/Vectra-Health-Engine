"""scripts/merge_real_data.py — Funde dados reais coletados no choropleth.

Combina os dados reais coletados pelos fetchers num score de risco
epidemiológico e atualiza os assets que o frontend consome:

    data/raw/infodengue/infodengue_nacional_snapshot.csv  (casos, Rt, nível, incidência)
    data/raw/satellite/cv_indices_municipios.csv          (NDVI, NDWI, ilha de calor)
    data/raw/inmet/inmet_clima_diario.csv                 (temperatura, chuva — opcional)

Atualiza (preservando municípios sem dado real com o valor sintético anterior):
    frontend/public/geo/risk-national.json   -> {s,c,i, real:true/false}
    frontend/public/geo/mun/{UF}.json        -> properties.score
    frontend/public/geo/manifest.json        -> adiciona estatísticas de cobertura real

Uso:
    python scripts/merge_real_data.py
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

GEO_DIR = Path("frontend/public/geo")
RISK_FILE = GEO_DIR / "risk-national.json"
MUN_DIR = GEO_DIR / "mun"
MANIFEST = GEO_DIR / "manifest.json"

INFODENGUE = Path("data/raw/infodengue/infodengue_nacional_snapshot.csv")
SATELLITE = Path("data/raw/satellite/cv_indices_municipios.csv")
INMET = Path("data/raw/inmet/inmet_clima_diario.csv")


def _norm_geocode(g) -> str:
    return str(g).split(".")[0].zfill(7)


def compute_risk_score(row: dict) -> float:
    """Score de risco 0-100 a partir de sinais reais (InfoDengue + CV).

    Pesos:
        40% incidência (p_inc100k) — pressão epidemiológica direta
        25% transmissão (Rt)       — Rt>1 indica crescimento
        15% nível de alerta InfoDengue (1-4)
        12% NDWI                   — água superficial / criadouros
         8% ilha de calor          — favorece o vetor
    """
    # incidência: satura em 100/100k = score alto
    inc = float(row.get("p_inc100k", 0) or 0)
    inc_score = min(100, inc * 1.2)

    # Rt: 0.5→0, 1.0→50, 2.0→100
    rt = float(row.get("Rt", 1.0) or 1.0)
    rt_score = float(np.clip((rt - 0.5) / 1.5 * 100, 0, 100))

    # nível InfoDengue (1=verde ... 4=vermelho)
    nivel = float(row.get("nivel", 1) or 1)
    nivel_score = (nivel - 1) / 3 * 100

    # NDWI: 0→0, 0.6→100
    ndwi = float(row.get("ndwi_mean", 0.3) or 0.3)
    ndwi_score = float(np.clip(ndwi / 0.6 * 100, 0, 100))

    # ilha de calor já é 0-100
    heat = float(row.get("heat_island_score", 50) or 50)

    score = (
        0.40 * inc_score +
        0.25 * rt_score +
        0.15 * nivel_score +
        0.12 * ndwi_score +
        0.08 * heat
    )
    return round(float(np.clip(score, 0, 99)), 1)


def load_real_signals() -> dict[str, dict]:
    """Carrega e funde os CSVs reais por geocode."""
    signals: dict[str, dict] = {}

    if INFODENGUE.exists():
        df = pd.read_csv(INFODENGUE, dtype={"geocode": str})
        df["geocode"] = df["geocode"].map(_norm_geocode)
        # fica com a semana mais recente por município
        if "SE" in df.columns:
            df = df.sort_values("SE").groupby("geocode", as_index=False).tail(1)
        for _, r in df.iterrows():
            signals.setdefault(r["geocode"], {}).update({
                "casos": r.get("casos"),
                "p_inc100k": r.get("p_inc100k"),
                "Rt": r.get("Rt"),
                "nivel": r.get("nivel"),
                "tempmed": r.get("tempmed"),
                "umidmed": r.get("umidmed"),
            })
        logger.info("InfoDengue: %d municípios com dado real.", len(df))
    else:
        logger.warning("InfoDengue não encontrado: %s", INFODENGUE)

    if SATELLITE.exists():
        df = pd.read_csv(SATELLITE, dtype={"geocode": str})
        df["geocode"] = df["geocode"].map(_norm_geocode)
        for _, r in df.iterrows():
            signals.setdefault(r["geocode"], {}).update({
                "ndvi_mean": r.get("ndvi_mean"),
                "ndwi_mean": r.get("ndwi_mean"),
                "heat_island_score": r.get("heat_island_score"),
            })
        logger.info("Satélite CV: %d municípios.", len(df))
    else:
        logger.warning("CV satélite não encontrado: %s", SATELLITE)

    return signals


def main() -> None:
    if not RISK_FILE.exists():
        raise FileNotFoundError("Rode scripts/build_geo_assets.py primeiro.")

    risk = json.loads(RISK_FILE.read_text(encoding="utf-8"))
    signals = load_real_signals()

    if not signals:
        logger.error("Nenhum dado real disponível. Rode os fetchers antes do merge.")
        return

    updated = 0
    real_scores: dict[str, float] = {}

    for geocode, sig in signals.items():
        if geocode not in risk:
            continue
        # só sobrescreve o score quando há dado epidemiológico real (InfoDengue);
        # CV satélite sozinho não rebaixa o baseline sintético.
        has_epi = any(sig.get(k) is not None and not pd.isna(sig.get(k)) for k in ("casos", "Rt", "p_inc100k"))
        if not has_epi:
            continue
        score = compute_risk_score(sig)
        casos = sig.get("casos")
        inc = sig.get("p_inc100k")
        risk[geocode]["s"] = score
        if casos is not None and not pd.isna(casos):
            risk[geocode]["c"] = int(float(casos))
        if inc is not None and not pd.isna(inc):
            risk[geocode]["i"] = round(float(inc), 1)
        risk[geocode]["real"] = True
        real_scores[geocode] = score
        updated += 1

    RISK_FILE.write_text(json.dumps(risk, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    logger.info("risk-national.json atualizado | %d municípios com dado real.", updated)

    # propaga scores reais para os polígonos por UF
    poly_updated = 0
    for uf_file in sorted(MUN_DIR.glob("*.json")):
        data = json.loads(uf_file.read_text(encoding="utf-8"))
        changed = False
        for f in data["features"]:
            gc = _norm_geocode(f["properties"].get("geocode", ""))
            if gc in real_scores:
                f["properties"]["score"] = real_scores[gc]
                f["properties"]["real"] = True
                changed = True
                poly_updated += 1
        if changed:
            uf_file.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    logger.info("Polígonos atualizados com score real: %d features.", poly_updated)

    # atualiza manifest
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        manifest["real_data"] = {
            "municipalities_with_real_score": updated,
            "coverage_pct": round(updated / max(1, len(risk)) * 100, 1),
            "sources": [s for s, p in [("infodengue", INFODENGUE), ("satellite_cv", SATELLITE), ("inmet", INMET)] if p.exists()],
        }
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        logger.info("Manifest: cobertura real %.1f%%", manifest["real_data"]["coverage_pct"])


if __name__ == "__main__":
    main()
