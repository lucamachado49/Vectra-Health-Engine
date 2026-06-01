"""
src/utils/date_utils.py — Utilitários de datas e semanas epidemiológicas.
"""
from __future__ import annotations
import pandas as pd

def add_epi_year_week_from_date(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """
    Cria colunas 'ano' e 'semana_epidemiologica' a partir de uma coluna de data.

    Usa semana ISO como aproximação da semana epidemiológica.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    iso = df[date_col].dt.isocalendar()
    df["ano"] = iso["year"].astype("Int64")
    df["semana_epidemiologica"] = iso["week"].astype("Int64")
    return df

def build_time_label(df: pd.DataFrame) -> pd.Series:
    """Cria rótulo textual 'YYYY-Www' para uso em gráficos."""
    return df["ano"].astype(str) + "-W" + df["semana_epidemiologica"].astype(str).str.zfill(2)
