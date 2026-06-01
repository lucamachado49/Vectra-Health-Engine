"""src/data/fetch_infodengue_national.py — Coleta InfoDengue em escala nacional.

Lê a lista de geocodes gerada por scripts/build_geo_assets.py
(frontend/public/geo/risk-national.json) e coleta o snapshot epidemiológico
mais recente de cada município via API pública InfoDengue.

Recursos:
    - Rate-limiting configurável (evita bloqueio da API).
    - Retomada: pula geocodes já salvos no CSV de saída.
    - Filtros por UF e limite para execução parcial.

Uso:
    python -m src.data.fetch_infodengue_national                 # todos
    python -m src.data.fetch_infodengue_national --ufs SP,BA     # alguns estados
    python -m src.data.fetch_infodengue_national --limit 200     # primeiros N

Saída:
    data/raw/infodengue/infodengue_nacional_snapshot.csv
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from src.config import INFODENGUE_BASE_URL

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

GEOCODES_FILE = Path("frontend/public/geo/risk-national.json")
OUTPUT_FILE = Path("data/raw/infodengue/infodengue_nacional_snapshot.csv")


def load_geocodes(ufs: list[str] | None = None) -> dict[str, dict]:
    """Carrega geocodes do arquivo de risco nacional."""
    if not GEOCODES_FILE.exists():
        raise FileNotFoundError(
            f"{GEOCODES_FILE} não existe. Rode primeiro: python scripts/build_geo_assets.py"
        )
    data = json.loads(GEOCODES_FILE.read_text(encoding="utf-8"))
    if ufs:
        data = {g: v for g, v in data.items() if v.get("uf") in ufs}
    return data


def _already_collected() -> set[str]:
    """Geocodes já presentes no CSV de saída (para retomada)."""
    if not OUTPUT_FILE.exists():
        return set()
    try:
        existing = pd.read_csv(OUTPUT_FILE, usecols=["geocode"], dtype=str)
        return set(existing["geocode"].astype(str))
    except Exception:  # noqa: BLE001
        return set()


def fetch_one(geocode: str, disease: str, year: int, timeout: int = 30) -> pd.DataFrame | None:
    """Coleta a última semana epidemiológica disponível de um município."""
    url = (
        f"{INFODENGUE_BASE_URL}?geocode={geocode}&disease={disease}"
        f"&format=csv&ew_start=1&ew_end=53&ey_start={year}&ey_end={year}"
    )
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text))
        if df.empty:
            return None
        df["geocode"] = str(geocode)
        df["disease"] = disease
        # mantém apenas a semana mais recente
        sort_cols = [c for c in ["data_iniSE", "SE"] if c in df.columns]
        if sort_cols:
            df = df.sort_values(sort_cols).tail(1)
        return df
    except Exception as exc:  # noqa: BLE001
        logger.debug("Falha geocode %s: %s", geocode, exc)
        return None


def run(
    ufs: list[str] | None = None,
    disease: str = "dengue",
    year: int = 2025,
    limit: int | None = None,
    sleep: float = 0.25,
    flush_every: int = 50,
) -> None:
    """Executa a coleta nacional com retomada e rate-limiting."""
    geocodes = load_geocodes(ufs)
    done = _already_collected()
    pending = [g for g in geocodes if g not in done]
    if limit:
        pending = pending[:limit]

    logger.info(
        "InfoDengue nacional | alvo=%d | já coletados=%d | pendentes=%d | doença=%s | ano=%d",
        len(geocodes), len(done), len(pending), disease, year,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    buffer: list[pd.DataFrame] = []
    ok = 0

    for i, geocode in enumerate(pending, 1):
        df = fetch_one(geocode, disease, year)
        if df is not None:
            buffer.append(df)
            ok += 1

        if i % flush_every == 0 or i == len(pending):
            if buffer:
                combined = pd.concat(buffer, ignore_index=True)
                header = not OUTPUT_FILE.exists()
                combined.to_csv(OUTPUT_FILE, mode="a", header=header, index=False, encoding="utf-8")
                buffer = []
            logger.info("Progresso: %d/%d | coletados ok=%d", i, len(pending), ok)

        time.sleep(sleep)

    logger.info("Concluído. Snapshot nacional salvo em %s | novos registros ok=%d", OUTPUT_FILE, ok)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ufs", default=None, help="UFs separadas por vírgula (ex: SP,BA). Padrão: todas.")
    parser.add_argument("--disease", default="dengue", choices=["dengue", "zika", "chikungunya"])
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.25, help="Pausa entre requisições (s).")
    args = parser.parse_args()

    ufs = [u.strip().upper() for u in args.ufs.split(",")] if args.ufs else None
    run(ufs=ufs, disease=args.disease, year=args.year, limit=args.limit, sleep=args.sleep)


if __name__ == "__main__":
    main()
