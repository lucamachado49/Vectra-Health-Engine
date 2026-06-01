"""Risk map helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


def build_risk_geojson_table(
    latest_risk: pd.DataFrame,
    geocode_col: str = "geocode",
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Prepare a compact table that can be joined to municipal GeoJSON."""
    keep_cols = [
        geocode_col,
        "municipio",
        "risk_label",
        "risco_ambiental_label",
        "probability_surto",
        "environmental_risk_score",
        "incidencia_100k",
        "casos_dengue",
    ]
    keep_cols = [col for col in keep_cols if col in latest_risk.columns]
    table = latest_risk[keep_cols].copy()
    table[geocode_col] = table[geocode_col].astype(str).str.replace(".0", "", regex=False).str.zfill(7)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(output_path, index=False, encoding="utf-8")

    return table


__all__ = ["build_risk_geojson_table"]
