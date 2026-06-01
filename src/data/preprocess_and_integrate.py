"""
Módulo 2 — Pré-processamento e Integração de Dados do Vectra Health

Caminho recomendado no projeto:
    src/data/preprocess_and_integrate.py

Objetivo:
    Transformar os arquivos brutos coletados no Módulo 1 em bases limpas, semanais
    e integradas para modelagem supervisionada.

Entradas esperadas:
    data/raw/infodengue/dengue_sp_selected_2020_2025_raw.csv
    data/raw/nasa_power/nasa_power_sao_paulo_2020_2025_raw.csv
    data/raw/ibge/populacao_municipios_2021_raw.csv
    data/raw/geo/municipios_sp_2020_raw.geojson

Saídas intermediárias:
    data/interim/dengue_clean.csv
    data/interim/climate_weekly.csv
    data/interim/population_clean.csv
    data/interim/vectra_health_integrated_weekly.csv

Saídas processadas:
    data/processed/vectra_health_weekly_municipality_dataset.csv

Observação importante:
    Este módulo ainda não cria o target final de machine learning.
    A definição do target, lags avançados e variáveis preditivas mais sofisticadas
    ficarão no Módulo 3 — Feature Engineering.
"""

from __future__ import annotations

import logging
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd


# ==========================================================
# Configuração de logging
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ==========================================================
# Configuração dos caminhos do projeto
# ==========================================================

@dataclass(frozen=True)
class ProjectPaths:
    """Centraliza os caminhos usados pelo pipeline de pré-processamento."""

    root_dir: Path = Path(".")

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
    def raw_infodengue_dir(self) -> Path:
        return self.raw_dir / "infodengue"

    @property
    def raw_nasa_power_dir(self) -> Path:
        return self.raw_dir / "nasa_power"

    @property
    def raw_ibge_dir(self) -> Path:
        return self.raw_dir / "ibge"

    @property
    def raw_geo_dir(self) -> Path:
        return self.raw_dir / "geo"

    def create_all(self) -> None:
        """Cria os diretórios necessários para as saídas do Módulo 2."""
        for folder in [self.interim_dir, self.processed_dir, self.processed_dir / "geo"]:
            folder.mkdir(parents=True, exist_ok=True)
            logger.info("Diretório verificado/criado: %s", folder)


# ==========================================================
# Funções utilitárias gerais
# ==========================================================

def normalize_column_name(column: str) -> str:
    """
    Normaliza nomes de colunas para snake_case sem acentos.

    Exemplo:
        "Casos Estimados" -> "casos_estimados"
    """
    column = str(column).strip().lower()
    column = unicodedata.normalize("NFKD", column)
    column = "".join(char for char in column if not unicodedata.combining(char))
    column = column.replace("/", "_").replace("-", "_").replace(" ", "_")
    column = column.replace(".", "_").replace("(", "").replace(")", "")

    while "__" in column:
        column = column.replace("__", "_")

    return column.strip("_")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica normalização de nomes de colunas em um DataFrame."""
    df = df.copy()
    df.columns = [normalize_column_name(col) for col in df.columns]
    return df


def read_csv_safely(path: Path) -> pd.DataFrame:
    """Lê CSV tentando alguns encodings comuns."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    encodings = ["utf-8", "utf-8-sig", "latin1"]
    last_error: Optional[Exception] = None

    for encoding in encodings:
        try:
            df = pd.read_csv(path, encoding=encoding)
            logger.info("CSV carregado: %s | encoding=%s | shape=%s", path, encoding, df.shape)
            return df
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    raise ValueError(f"Não foi possível ler o arquivo {path}. Último erro: {last_error}")


def save_dataframe(df: pd.DataFrame, output_path: Path) -> None:
    """Salva DataFrame em CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Arquivo salvo: %s | shape=%s", output_path, df.shape)


def first_existing_column(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    """
    Retorna a primeira coluna existente entre nomes candidatos.

    Útil porque APIs públicas podem mudar nomes de colunas ou retornar campos
    levemente diferentes conforme período/endpoint.
    """
    normalized_candidates = [normalize_column_name(col) for col in candidates]
    for col in normalized_candidates:
        if col in df.columns:
            return col
    return None


def coerce_numeric_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Converte colunas para numérico quando existirem."""
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def add_epi_year_week_from_date(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """
    Cria ano e semana epidemiológica aproximados a partir de uma data.

    Para simplificação técnica do projeto, utiliza semana ISO.
    Em contextos epidemiológicos profissionais, pode ser necessário usar
    calendário epidemiológico oficial do Ministério da Saúde.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    iso = df[date_col].dt.isocalendar()
    df["ano"] = iso["year"].astype("Int64")
    df["semana_epidemiologica"] = iso["week"].astype("Int64")
    return df


# ==========================================================
# 1. Pré-processamento InfoDengue
# ==========================================================

def clean_infodengue_data(input_path: Path, output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Limpa a base bruta do InfoDengue.

    Etapas:
        1. Normaliza nomes das colunas.
        2. Padroniza geocode como string.
        3. Identifica colunas de ano e semana epidemiológica.
        4. Converte colunas epidemiológicas para numérico.
        5. Cria campos auxiliares para modelagem.

    Args:
        input_path: Caminho do CSV bruto do InfoDengue.
        output_path: Caminho opcional para salvar o CSV limpo.

    Returns:
        DataFrame limpo.
    """
    df = read_csv_safely(input_path)
    df = normalize_columns(df)

    # Padronização de geocode.
    if "geocode" not in df.columns:
        possible_geocode = first_existing_column(df, ["cod_mun", "municipio_geocodigo", "ibge", "id_municipio"])
        if possible_geocode is None:
            raise ValueError("Não foi possível identificar a coluna geocode no InfoDengue.")
        df = df.rename(columns={possible_geocode: "geocode"})

    df["geocode"] = df["geocode"].astype(str).str.replace(".0", "", regex=False).str.zfill(7)

    # Padronização de ano epidemiológico.
    year_col = first_existing_column(df, ["ano", "year", "ey", "ano_epidemiologico"])
    if year_col is not None and year_col != "ano":
        df = df.rename(columns={year_col: "ano"})

    # Padronização de semana epidemiológica.
    week_col = first_existing_column(df, ["semana_epidemiologica", "se", "semana", "ew"])
    if week_col is not None and week_col != "semana_epidemiologica":
        df = df.rename(columns={week_col: "semana_epidemiologica"})

    # Quando houver data de início da semana, cria ano/semana caso não existam.
    date_col = first_existing_column(df, ["data_inise", "data_inicio_semana", "data_ini_se", "date"])
    if date_col is not None:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        if "ano" not in df.columns or "semana_epidemiologica" not in df.columns:
            df = add_epi_year_week_from_date(df, date_col)
        df = df.rename(columns={date_col: "data_inicio_semana"})

    if "ano" not in df.columns or "semana_epidemiologica" not in df.columns:
        raise ValueError(
            "A base InfoDengue precisa conter ano e semana epidemiológica "
            "ou uma coluna de data para derivação."
        )

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["semana_epidemiologica"] = pd.to_numeric(
        df["semana_epidemiologica"], errors="coerce"
    ).astype("Int64")

    # Colunas epidemiológicas e climáticas potencialmente retornadas pelo InfoDengue.
    numeric_candidates = [
        "casos",
        "casos_est",
        "casos_estimados",
        "casos_notificados",
        "nivel",
        "tempmin",
        "tempmed",
        "tempmax",
        "umidmin",
        "umidmed",
        "umidmax",
        "receptivo",
        "transmissao",
        "tweet",
        "rt",
        "pop",
    ]
    df = coerce_numeric_columns(df, numeric_candidates)

    # Padroniza a coluna principal de casos.
    if "casos_dengue" not in df.columns:
        cases_col = first_existing_column(df, ["casos", "casos_est", "casos_estimados", "casos_notificados"])
        if cases_col is not None:
            df["casos_dengue"] = pd.to_numeric(df[cases_col], errors="coerce")
        else:
            logger.warning("Nenhuma coluna de casos foi encontrada no InfoDengue.")
            df["casos_dengue"] = np.nan

    # Mantém disease se existir; caso contrário, assume dengue.
    if "disease" not in df.columns:
        df["disease"] = "dengue"

    # Remove linhas sem chave temporal/espacial.
    before = len(df)
    df = df.dropna(subset=["geocode", "ano", "semana_epidemiologica"])
    after = len(df)
    logger.info("InfoDengue limpo | linhas removidas por chave ausente: %s", before - after)

    # Ordenação para facilitar inspeção.
    df = df.sort_values(["geocode", "ano", "semana_epidemiologica"]).reset_index(drop=True)

    if output_path is not None:
        save_dataframe(df, output_path)

    return df


# ==========================================================
# 2. Pré-processamento NASA POWER
# ==========================================================

def clean_nasa_power_daily(input_path: Path) -> pd.DataFrame:
    """
    Limpa a base diária da NASA POWER.

    Args:
        input_path: Caminho do CSV diário bruto da NASA POWER.

    Returns:
        DataFrame diário limpo.
    """
    df = read_csv_safely(input_path)
    df = normalize_columns(df)

    if "date" not in df.columns:
        date_col = first_existing_column(df, ["data", "datetime", "dia"])
        if date_col is None:
            raise ValueError("Não foi possível identificar coluna de data na NASA POWER.")
        df = df.rename(columns={date_col: "date"})

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    if "geocode" not in df.columns:
        logger.warning(
            "NASA POWER sem coluna geocode. Será necessário informar ou integrar por coordenada posteriormente."
        )
        df["geocode"] = "unknown"
    else:
        df["geocode"] = df["geocode"].astype(str).str.replace(".0", "", regex=False).str.zfill(7)

    if "municipio" not in df.columns:
        df["municipio"] = "não informado"

    # Variáveis mais comuns do NASA POWER.
    climate_cols = ["t2m", "t2m_max", "t2m_min", "rh2m", "prectotcorr", "ws2m"]
    df = coerce_numeric_columns(df, climate_cols)

    before = len(df)
    df = df.dropna(subset=["date"])
    after = len(df)
    logger.info("NASA POWER diário limpo | linhas removidas sem data: %s", before - after)

    return df.sort_values(["geocode", "date"]).reset_index(drop=True)


def aggregate_climate_daily_to_weekly(
    daily_df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Agrega dados climáticos diários para granularidade semanal.

    Agregações:
        - temperatura média semanal;
        - temperatura máxima semanal;
        - temperatura mínima semanal;
        - umidade média semanal;
        - chuva acumulada semanal;
        - quantidade de dias com chuva.

    Args:
        daily_df: DataFrame diário limpo da NASA POWER.
        output_path: Caminho opcional para salvar CSV semanal.

    Returns:
        DataFrame semanal.
    """
    df = daily_df.copy()
    df = add_epi_year_week_from_date(df, "date")

    aggregation: dict[str, tuple[str, str]] = {}

    if "t2m" in df.columns:
        aggregation["temp_media_7d"] = ("t2m", "mean")
    if "t2m_max" in df.columns:
        aggregation["temp_max_7d"] = ("t2m_max", "max")
    if "t2m_min" in df.columns:
        aggregation["temp_min_7d"] = ("t2m_min", "min")
    if "rh2m" in df.columns:
        aggregation["umidade_media_7d"] = ("rh2m", "mean")
    if "prectotcorr" in df.columns:
        aggregation["chuva_acumulada_7d"] = ("prectotcorr", "sum")
        df["dia_com_chuva"] = np.where(df["prectotcorr"].fillna(0) > 0, 1, 0)
        aggregation["dias_com_chuva_7d"] = ("dia_com_chuva", "sum")
    if "ws2m" in df.columns:
        aggregation["vento_medio_7d"] = ("ws2m", "mean")

    if not aggregation:
        raise ValueError("Nenhuma variável climática reconhecida foi encontrada para agregação semanal.")

    weekly = (
        df.groupby(["geocode", "municipio", "ano", "semana_epidemiologica"], as_index=False)
        .agg(**aggregation)
        .sort_values(["geocode", "ano", "semana_epidemiologica"])
        .reset_index(drop=True)
    )

    # Arredondamento para deixar os CSVs mais legíveis.
    numeric_cols = weekly.select_dtypes(include=["float", "float64"]).columns
    weekly[numeric_cols] = weekly[numeric_cols].round(4)

    if output_path is not None:
        save_dataframe(weekly, output_path)

    return weekly


# ==========================================================
# 3. Pré-processamento população IBGE
# ==========================================================

def clean_population_data(input_path: Path, output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Limpa a base de população municipal do IBGE/SIDRA.

    Args:
        input_path: Caminho do CSV bruto de população.
        output_path: Caminho opcional para salvar CSV limpo.

    Returns:
        DataFrame limpo com geocode, municipio e populacao.
    """
    df = read_csv_safely(input_path)
    df = normalize_columns(df)

    # Ajustes defensivos para diferentes possíveis retornos da API SIDRA.
    if "geocode" not in df.columns:
        geocode_col = first_existing_column(df, ["d1c", "codigo_municipio", "cod_mun", "municipio_codigo"])
        if geocode_col is None:
            raise ValueError("Não foi possível identificar geocode na base de população.")
        df = df.rename(columns={geocode_col: "geocode"})

    if "municipio" not in df.columns:
        city_col = first_existing_column(df, ["d1n", "nome_municipio", "municipio_nome", "localidade"])
        if city_col is not None:
            df = df.rename(columns={city_col: "municipio"})
        else:
            df["municipio"] = "não informado"

    if "populacao" not in df.columns:
        pop_col = first_existing_column(df, ["v", "valor", "population", "pop"])
        if pop_col is None:
            raise ValueError("Não foi possível identificar a coluna de população.")
        df = df.rename(columns={pop_col: "populacao"})

    df["geocode"] = df["geocode"].astype(str).str.replace(".0", "", regex=False).str.zfill(7)
    df["populacao"] = (
        df["populacao"]
        .astype(str)
        .str.replace(" ", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df["populacao"] = pd.to_numeric(df["populacao"], errors="coerce")

    keep_cols = [col for col in ["geocode", "municipio", "populacao", "ano"] if col in df.columns]
    df = df[keep_cols].drop_duplicates(subset=["geocode"]).reset_index(drop=True)

    before = len(df)
    df = df.dropna(subset=["geocode", "populacao"])
    after = len(df)
    logger.info("População limpa | linhas removidas sem população: %s", before - after)

    if output_path is not None:
        save_dataframe(df, output_path)

    return df


# ==========================================================
# 4. Integração das bases
# ==========================================================

def integrate_weekly_dataset(
    dengue_df: pd.DataFrame,
    climate_weekly_df: pd.DataFrame,
    population_df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Integra dados epidemiológicos, climáticos e populacionais.

    A chave principal é:
        geocode + ano + semana_epidemiologica

    Args:
        dengue_df: Base limpa do InfoDengue.
        climate_weekly_df: Base climática semanal.
        population_df: Base populacional limpa.
        output_path: Caminho opcional para salvar a base integrada.

    Returns:
        DataFrame semanal integrado.
    """
    dengue = dengue_df.copy()
    climate = climate_weekly_df.copy()
    population = population_df.copy()

    # Garantia de tipos padronizados.
    for frame in [dengue, climate, population]:
        if "geocode" in frame.columns:
            frame["geocode"] = frame["geocode"].astype(str).str.replace(".0", "", regex=False).str.zfill(7)

    for frame in [dengue, climate]:
        frame["ano"] = pd.to_numeric(frame["ano"], errors="coerce").astype("Int64")
        frame["semana_epidemiologica"] = pd.to_numeric(
            frame["semana_epidemiologica"], errors="coerce"
        ).astype("Int64")

    # Seleção inicial de colunas úteis da dengue.
    dengue_cols = [
        "geocode",
        "ano",
        "semana_epidemiologica",
        "data_inicio_semana",
        "disease",
        "casos_dengue",
        "casos_est",
        "casos_estimados",
        "nivel",
        "tempmin",
        "tempmed",
        "tempmax",
        "umidmin",
        "umidmed",
        "umidmax",
    ]
    dengue_cols = [col for col in dengue_cols if col in dengue.columns]
    dengue = dengue[dengue_cols].copy()

    # Agregação defensiva caso exista mais de uma linha por município/semana.
    numeric_cols = dengue.select_dtypes(include=["number", "Int64", "Float64"]).columns.tolist()
    numeric_cols = [col for col in numeric_cols if col not in ["ano", "semana_epidemiologica"]]

    group_cols = ["geocode", "ano", "semana_epidemiologica"]
    agg_dict: dict[str, str] = {col: "mean" for col in numeric_cols}

    if "data_inicio_semana" in dengue.columns:
        agg_dict["data_inicio_semana"] = "first"
    if "disease" in dengue.columns:
        agg_dict["disease"] = "first"

    dengue = dengue.groupby(group_cols, as_index=False).agg(agg_dict)

    # Integra clima.
    integrated = dengue.merge(
        climate,
        on=["geocode", "ano", "semana_epidemiologica"],
        how="left",
        suffixes=("", "_nasa"),
    )

    # Integra população.
    population_cols = [col for col in ["geocode", "municipio", "populacao"] if col in population.columns]
    integrated = integrated.merge(population[population_cols], on="geocode", how="left", suffixes=("", "_ibge"))

    # Resolve município caso tenha vindo da NASA e do IBGE.
    if "municipio_ibge" in integrated.columns and "municipio" in integrated.columns:
        integrated["municipio"] = integrated["municipio"].fillna(integrated["municipio_ibge"])
        integrated = integrated.drop(columns=["municipio_ibge"])

    # Incidência por 100 mil habitantes.
    if "casos_dengue" in integrated.columns and "populacao" in integrated.columns:
        integrated["incidencia_100k"] = (
            integrated["casos_dengue"] / integrated["populacao"] * 100_000
        ).replace([np.inf, -np.inf], np.nan)

    # Score climático simples, apenas exploratório, para ajudar o dashboard inicial.
    # O score final de risco será desenvolvido no Módulo 3/4 com ML supervisionado.
    integrated = add_basic_environmental_risk_score(integrated)

    # Ordena colunas principais no início.
    priority_cols = [
        "geocode",
        "municipio",
        "ano",
        "semana_epidemiologica",
        "data_inicio_semana",
        "disease",
        "casos_dengue",
        "incidencia_100k",
        "populacao",
        "temp_media_7d",
        "temp_max_7d",
        "temp_min_7d",
        "umidade_media_7d",
        "chuva_acumulada_7d",
        "dias_com_chuva_7d",
        "environmental_risk_score",
    ]
    ordered_cols = [col for col in priority_cols if col in integrated.columns]
    remaining_cols = [col for col in integrated.columns if col not in ordered_cols]
    integrated = integrated[ordered_cols + remaining_cols]

    # Arredondamento geral.
    float_cols = integrated.select_dtypes(include=["float", "float64"]).columns
    integrated[float_cols] = integrated[float_cols].round(4)

    integrated = integrated.sort_values(["geocode", "ano", "semana_epidemiologica"]).reset_index(drop=True)

    if output_path is not None:
        save_dataframe(integrated, output_path)

    logger.info("Dataset integrado criado | shape=%s", integrated.shape)
    return integrated


def add_basic_environmental_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria um score ambiental simples para exploração e protótipo.

    Este score NÃO substitui o modelo supervisionado.
    Ele serve para:
        - criar visualizações iniciais;
        - alimentar protótipo React;
        - apoiar análise exploratória;
        - demonstrar lógica de risco ambiental.

    Lógica simplificada:
        - maior temperatura média aumenta risco;
        - maior umidade aumenta risco;
        - maior chuva acumulada aumenta risco;
        - valores são normalizados entre 0 e 1 por percentil.
    """
    df = df.copy()

    score_features = [
        "temp_media_7d",
        "umidade_media_7d",
        "chuva_acumulada_7d",
    ]
    available_features = [col for col in score_features if col in df.columns]

    if not available_features:
        df["environmental_risk_score"] = np.nan
        return df

    normalized_parts = []
    for col in available_features:
        series = pd.to_numeric(df[col], errors="coerce")
        min_value = series.quantile(0.05)
        max_value = series.quantile(0.95)

        if pd.isna(min_value) or pd.isna(max_value) or min_value == max_value:
            normalized = pd.Series(np.nan, index=df.index)
        else:
            normalized = ((series - min_value) / (max_value - min_value)).clip(0, 1)

        normalized_parts.append(normalized)

    df["environmental_risk_score"] = pd.concat(normalized_parts, axis=1).mean(axis=1)
    df["environmental_risk_score"] = (df["environmental_risk_score"] * 100).round(2)

    return df


# ==========================================================
# 5. Preparação do arquivo para o dashboard/mapa
# ==========================================================

def build_latest_risk_snapshot(
    integrated_df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Gera um recorte mais recente por município para alimentar o dashboard.

    Args:
        integrated_df: Dataset integrado semanal.
        output_path: Caminho opcional para salvar o snapshot.

    Returns:
        DataFrame com a última semana disponível por município.
    """
    df = integrated_df.copy()
    df = df.dropna(subset=["ano", "semana_epidemiologica"])
    df = df.sort_values(["geocode", "ano", "semana_epidemiologica"])

    latest = df.groupby("geocode", as_index=False).tail(1).reset_index(drop=True)

    # Classificação exploratória para protótipo visual.
    if "environmental_risk_score" in latest.columns:
        latest["risco_ambiental_label"] = pd.cut(
            latest["environmental_risk_score"],
            bins=[-np.inf, 33, 66, np.inf],
            labels=["baixo", "médio", "alto"],
        ).astype(str)

    if output_path is not None:
        save_dataframe(latest, output_path)

    return latest


# ==========================================================
# 6. Execução principal do Módulo 2
# ==========================================================

def run_preprocessing_pipeline(root_dir: Path = Path(".")) -> pd.DataFrame:
    """
    Executa o pipeline completo do Módulo 2.

    Args:
        root_dir: Diretório raiz do projeto.

    Returns:
        Dataset integrado final em memória.
    """
    paths = ProjectPaths(root_dir=root_dir)
    paths.create_all()

    # Entradas seguindo a estrutura definida no Módulo 1.
    infodengue_path = paths.raw_infodengue_dir / "dengue_sp_selected_2020_2025_raw.csv"
    nasa_power_path = paths.raw_nasa_power_dir / "nasa_power_sao_paulo_2020_2025_raw.csv"
    population_path = paths.raw_ibge_dir / "populacao_municipios_2021_raw.csv"

    logger.info("=== Limpando InfoDengue ===")
    dengue_clean = clean_infodengue_data(
        input_path=infodengue_path,
        output_path=paths.interim_dir / "dengue_clean.csv",
    )

    logger.info("=== Limpando NASA POWER diário ===")
    nasa_daily = clean_nasa_power_daily(input_path=nasa_power_path)

    logger.info("=== Agregando NASA POWER para semana epidemiológica ===")
    climate_weekly = aggregate_climate_daily_to_weekly(
        daily_df=nasa_daily,
        output_path=paths.interim_dir / "climate_weekly.csv",
    )

    logger.info("=== Limpando população IBGE ===")
    population_clean = clean_population_data(
        input_path=population_path,
        output_path=paths.interim_dir / "population_clean.csv",
    )

    logger.info("=== Integrando bases ===")
    integrated = integrate_weekly_dataset(
        dengue_df=dengue_clean,
        climate_weekly_df=climate_weekly,
        population_df=population_clean,
        output_path=paths.interim_dir / "vectra_health_integrated_weekly.csv",
    )

    logger.info("=== Salvando dataset processado principal ===")
    save_dataframe(
        integrated,
        paths.processed_dir / "vectra_health_weekly_municipality_dataset.csv",
    )

    logger.info("=== Gerando snapshot para dashboard ===")
    build_latest_risk_snapshot(
        integrated,
        output_path=paths.processed_dir / "vectra_health_latest_risk_snapshot.csv",
    )

    logger.info("Módulo 2 concluído com sucesso.")
    return integrated


if __name__ == "__main__":
    run_preprocessing_pipeline(root_dir=Path("."))
