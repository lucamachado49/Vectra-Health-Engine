"""
src/data/fetch_geodata.py — Coleta de dados geoespaciais via geobr.

Baixa malha municipal em GeoJSON para visualização e análise espacial.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def fetch_municipality_geodata(
    state_abbrev: str = "SP",
    year: int = 2020,
    output_path: Optional[Path] = None,
) -> None:
    """
    Baixa malha municipal via geobr e salva como GeoJSON.

    Args:
        state_abbrev: Sigla da UF (SP, RJ, MG...).
        year: Ano da malha geográfica.
        output_path: Caminho de saída do GeoJSON.
    """
    try:
        import geobr
    except ImportError as exc:
        raise ImportError("Instale geobr: pip install geobr") from exc

    logger.info("Baixando malha municipal | UF=%s | ano=%s", state_abbrev, year)
    gdf = geobr.read_municipality(code_muni=state_abbrev, year=year)
    if output_path is None:
        output_path = Path("data/raw/geo") / f"municipios_{state_abbrev.lower()}_{year}_raw.geojson"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver="GeoJSON")
    logger.info("GeoJSON salvo: %s | linhas=%s", output_path, len(gdf))
