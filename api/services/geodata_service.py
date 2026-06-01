"""
api/services/geodata_service.py — Serviço de dados geoespaciais do Vectra Health.

Responsável por:
    - Carregar o GeoJSON de risco municipal processado.
    - Servir dados geoespaciais para o frontend.
    - Integrar risco previsto ao GeoJSON.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class GeodataService:
    """Serviço de dados geoespaciais do Vectra Health."""

    def __init__(self, root_dir: Path = Path(".")) -> None:
        self.root_dir = root_dir
        self.geojson_path = root_dir / "data" / "processed" / "geo" / "vectra_municipios_risk.geojson"
        self.raw_geojson_path = root_dir / "data" / "raw" / "geo" / "municipios_sp_2020_raw.geojson"
        self._geojson: Optional[dict[str, Any]] = None

    def load_geojson(self) -> None:
        """Carrega GeoJSON de risco se existir."""
        path = self.geojson_path if self.geojson_path.exists() else self.raw_geojson_path
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                self._geojson = json.load(f)
            logger.info("GeoJSON carregado: %s", path)
        else:
            logger.warning("GeoJSON não encontrado em %s ou %s", self.geojson_path, self.raw_geojson_path)

    def get_geojson(self) -> Optional[dict[str, Any]]:
        """Retorna GeoJSON carregado."""
        if self._geojson is None:
            self.load_geojson()
        return self._geojson
