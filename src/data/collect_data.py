"""
src/data/collect_data.py — Orquestrador de coleta de dados do Vectra Health.

Este módulo coordena a coleta de todas as fontes de dados públicas.
A lógica específica de cada fonte está nos módulos fetch_*:

    src/data/fetch_infodengue.py  — InfoDengue/AlertaDengue
    src/data/fetch_nasa_power.py  — NASA POWER API
    src/data/fetch_ibge.py        — IBGE SIDRA (população)
    src/data/fetch_geodata.py     — geobr (malha municipal)

Entradas:
    Nenhuma (coleta diretamente das APIs públicas).

Saídas:
    data/raw/infodengue/dengue_sp_selected_2020_2025_raw.csv
    data/raw/nasa_power/nasa_power_sao_paulo_2020_2025_raw.json
    data/raw/nasa_power/nasa_power_sao_paulo_2020_2025_raw.csv
    data/raw/ibge/populacao_municipios_2021_raw.csv
    data/raw/geo/municipios_sp_2020_raw.geojson
"""
from __future__ import annotations

import logging
from pathlib import Path

from src.config import PATHS, DEFAULT_GEOCODES_SP
from src.data.fetch_infodengue import fetch_infodengue_for_many_cities
from src.data.fetch_nasa_power import fetch_nasa_power_daily_point, nasa_power_json_to_dataframe
from src.data.fetch_ibge import fetch_ibge_population_sidra
from src.data.fetch_geodata import fetch_municipality_geodata
from src.data.fetch_snis import fetch_snis_indicators
from src.data.fetch_google_trends import fetch_google_trends_symptoms
from src.data.fetch_mobility import fetch_mobility_flows
from src.utils.io_utils import save_dataframe, save_json

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def run_initial_data_collection(root_dir: Path = PATHS.root_dir) -> None:
    """
    Executa a coleta inicial de dados para o Vectra Health.

    Coleta dados epidemiológicos, climáticos, populacionais e geoespaciais
    para municípios representativos do estado de São Paulo (2020-2025).

    Args:
        root_dir: Diretório raiz do projeto.
    """
    from src.config import ProjectPaths
    paths = ProjectPaths(root_dir=root_dir)
    paths.create_all()

    logger.info("=== Coletando InfoDengue ===")
    dengue_df = fetch_infodengue_for_many_cities(
        geocodes=DEFAULT_GEOCODES_SP,
        disease="dengue",
        ey_start=2020,
        ey_end=2025,
    )
    save_dataframe(dengue_df, paths.raw_infodengue_dir / "dengue_sp_selected_2020_2025_raw.csv")

    logger.info("=== Coletando NASA POWER para São Paulo ===")
    nasa_payload = fetch_nasa_power_daily_point(
        latitude=-23.5505,
        longitude=-46.6333,
        start="20200101",
        end="20251231",
    )
    save_json(nasa_payload, paths.raw_nasa_power_dir / "nasa_power_sao_paulo_2020_2025_raw.json")
    nasa_df = nasa_power_json_to_dataframe(payload=nasa_payload, geocode="3550308", municipio="São Paulo")
    save_dataframe(nasa_df, paths.raw_nasa_power_dir / "nasa_power_sao_paulo_2020_2025_raw.csv")

    logger.info("=== Coletando população IBGE ===")
    population_df = fetch_ibge_population_sidra(year=2021)
    save_dataframe(population_df, paths.raw_ibge_dir / "populacao_municipios_2021_raw.csv")

    logger.info("=== Coletando GeoJSON municipal ===")
    fetch_municipality_geodata(
        state_abbrev="SP",
        year=2020,
        output_path=paths.raw_geo_dir / "municipios_sp_2020_raw.geojson",
    )

    logger.info("=== Coletando SNIS (saneamento básico) ===")
    snis_df = fetch_snis_indicators(geocodes=DEFAULT_GEOCODES_SP, year=2022)
    save_dataframe(snis_df, paths.raw_dir / "snis" / "snis_sp_2022_raw.csv")

    logger.info("=== Coletando Google Trends (sensores sociais) ===")
    trends_df = fetch_google_trends_symptoms(
        geocodes=DEFAULT_GEOCODES_SP,
        start_date="2024-01-01",
    )
    save_dataframe(trends_df, paths.raw_dir / "social" / "google_trends_dengue_sp_raw.csv")

    logger.info("=== Coletando mobilidade (fluxo populacional) ===")
    mobility_df = fetch_mobility_flows(geocodes=DEFAULT_GEOCODES_SP)
    save_dataframe(mobility_df, paths.raw_dir / "mobility" / "mobilidade_gravitacional_sp_raw.csv")

    logger.info("Coleta inicial concluída.")


if __name__ == "__main__":
    run_initial_data_collection()
