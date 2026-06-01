"""
src/utils/io_utils.py — Utilitários de I/O do Vectra Health.

Funções reutilizáveis para leitura e escrita de arquivos CSV, JSON e GeoJSON.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

def read_csv_safely(path: Path) -> pd.DataFrame:
    """Lê CSV tentando encodings utf-8, utf-8-sig e latin1."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    for encoding in ["utf-8", "utf-8-sig", "latin1"]:
        try:
            df = pd.read_csv(path, encoding=encoding)
            logger.info("CSV carregado: %s | encoding=%s | shape=%s", path, encoding, df.shape)
            return df
        except Exception:
            pass
    raise ValueError(f"Não foi possível ler o arquivo: {path}")

def save_dataframe(df: pd.DataFrame, output_path: Path) -> None:
    """Salva DataFrame como CSV UTF-8."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("CSV salvo: %s | shape=%s", output_path, df.shape)

def save_json(payload: dict, output_path: Path) -> None:
    """Salva dicionário como JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info("JSON salvo: %s", output_path)

def read_json_if_exists(path: Path) -> Optional[dict]:
    """Lê JSON se existir; caso contrário retorna None."""
    if not path.exists():
        logger.warning("JSON não encontrado: %s", path)
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def read_csv_if_exists(path: Path) -> Optional[pd.DataFrame]:
    """Lê CSV se existir; caso contrário retorna None."""
    if not path.exists():
        logger.warning("CSV não encontrado: %s", path)
        return None
    return read_csv_safely(path)
