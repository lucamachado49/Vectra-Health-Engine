"""
src/utils/geo_utils.py — Utilitários geoespaciais do Vectra Health.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

def standardize_geocode(series: pd.Series) -> pd.Series:
    """Padroniza geocode: remove .0 e faz zfill(7)."""
    return series.astype(str).str.replace(".0", "", regex=False).str.zfill(7)

def standardize_geocode_df(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza geocode in-place no DataFrame."""
    if "geocode" in df.columns:
        df = df.copy()
        df["geocode"] = standardize_geocode(df["geocode"])
    return df

def normalize_column_name(column: str) -> str:
    """
    Normaliza nomes de colunas para snake_case sem acentos.

    Exemplo: 'Casos Estimados' -> 'casos_estimados'
    """
    import unicodedata
    column = str(column).strip().lower()
    column = unicodedata.normalize("NFKD", column)
    column = "".join(c for c in column if not unicodedata.combining(c))
    for char, rep in [("/", "_"), ("-", "_"), (" ", "_"), (".", "_"), ("(", ""), (")", "")]:
        column = column.replace(char, rep)
    while "__" in column:
        column = column.replace("__", "_")
    return column.strip("_")

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica normalize_column_name em todos os nomes de colunas."""
    df = df.copy()
    df.columns = [normalize_column_name(c) for c in df.columns]
    return df
