"""
src/config.py — Configuração central do Vectra Health.

Centraliza caminhos, constantes e configurações de ambiente usadas em todo o projeto.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import os

ROOT_DIR: Path = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class ProjectPaths:
    """Centraliza todos os caminhos do projeto."""
    root_dir: Path = ROOT_DIR

    # Data
    @property
    def data_dir(self) -> Path:
        return self.root_dir / "data"
    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"
    @property
    def interim_dir(self) -> Path:
        return self.data_dir / "interim"
    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"
    @property
    def external_dir(self) -> Path:
        return self.data_dir / "external"

    # Raw subdirs
    @property
    def raw_infodengue_dir(self) -> Path:
        return self.raw_dir / "infodengue"
    @property
    def raw_nasa_power_dir(self) -> Path:
        return self.raw_dir / "nasa_power"
    @property
    def raw_ibge_dir(self) -> Path:
        return self.raw_dir / "ibge"
    @property
    def raw_datasus_dir(self) -> Path:
        return self.raw_dir / "datasus"
    @property
    def raw_geo_dir(self) -> Path:
        return self.raw_dir / "geo"

    # Models
    @property
    def models_dir(self) -> Path:
        return self.root_dir / "models"

    # Reports
    @property
    def reports_dir(self) -> Path:
        return self.root_dir / "reports"
    @property
    def figures_dir(self) -> Path:
        return self.reports_dir / "figures"
    @property
    def tables_dir(self) -> Path:
        return self.reports_dir / "tables"
    @property
    def summary_dir(self) -> Path:
        return self.reports_dir / "summary"

    # API agent logs
    @property
    def agent_logs_dir(self) -> Path:
        return self.processed_dir / "agent_logs"

    def create_all(self) -> None:
        """Cria todos os diretórios necessários."""
        dirs = [
            self.raw_infodengue_dir, self.raw_nasa_power_dir,
            self.raw_ibge_dir, self.raw_datasus_dir, self.raw_geo_dir,
            self.raw_dir / "snis",
            self.raw_dir / "social",
            self.raw_dir / "mobility",
            self.interim_dir, self.processed_dir, self.processed_dir / "geo",
            self.external_dir, self.models_dir,
            self.figures_dir, self.tables_dir, self.summary_dir,
            self.agent_logs_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

PATHS = ProjectPaths()

# Constantes epidemiológicas
DEFAULT_GEOCODES_SP = [
    "3550308",  # São Paulo
    "3509502",  # Campinas
    "3518800",  # Guarulhos
    "3543402",  # Ribeirão Preto
    "3548500",  # Santos
    "3534401",  # Osasco
    "3513801",  # Santo André
    "3549904",  # São Bernardo do Campo
    "3552205",  # Sorocaba
    "3506003",  # Bauru
    "3529401",  # Mogi das Cruzes
    "3547304",  # São José dos Campos
    "3541000",  # Piracicaba
    "3503307",  # Araras
    "3549805",  # São Carlos
]
INFODENGUE_BASE_URL = "https://info.dengue.mat.br/api/alertcity"
NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
IBGE_SIDRA_BASE_URL = "https://apisidra.ibge.gov.br/values"

# LLM
LLM_MODEL = os.getenv("VECTRA_LLM_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
