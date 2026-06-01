"""
Módulo 3 — Feature Engineering do Vectra Health

Caminho recomendado no projeto:
    src/features/build_features.py

Objetivo:
    Transformar o dataset integrado semanal em uma base de modelagem supervisionada,
    criando variáveis preditivas e targets para previsão de risco de surto.

Entrada principal:
    data/processed/vectra_health_weekly_municipality_dataset.csv

Entrada opcional:
    data/processed/computer_vision/cv_features.csv

Saídas:
    data/processed/vectra_health_features.csv
    data/processed/vectra_health_train_ready.csv
    data/processed/feature_metadata.csv

Principais grupos de features:
    1. Epidemiológicas:
        - casos_lag_1w
        - casos_lag_2w
        - media_casos_4w
        - crescimento_casos_2w
        - tendencia_casos_4w

    2. Climáticas:
        - chuva_acumulada_14d
        - chuva_acumulada_21d
        - temp_media_2w
        - umidade_media_2w
        - anomalia_temp
        - anomalia_chuva

    3. Populacionais e operacionais:
        - incidencia_100k
        - log_populacao
        - vulnerabilidade_operacional_proxy

    4. Visão computacional, quando disponível:
        - water_area_pct
        - vegetation_area_pct
        - critical_area_pct
        - ndvi_mean
        - ndwi_mean

Targets:
    - target_surto_binario
    - risco_surto_multiclasse
    - casos_dengue_next_1w
    - incidencia_100k_next_1w

Observação:
    Este módulo não treina modelos. Ele prepara a base para o Módulo 4 — Modelagem.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd


# ==========================================================
# Logging
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ==========================================================
# Caminhos do projeto
# ==========================================================

@dataclass(frozen=True)
class FeaturePaths:
    """Centraliza caminhos utilizados no Módulo 3."""

    root_dir: Path = Path(".")

    @property
    def processed_dir(self) -> Path:
        return self.root_dir / "data" / "processed"

    @property
    def cv_processed_dir(self) -> Path:
        return self.processed_dir / "computer_vision"

    @property
    def input_dataset_path(self) -> Path:
        return self.processed_dir / "vectra_health_weekly_municipality_dataset.csv"

    @property
    def cv_features_path(self) -> Path:
        return self.cv_processed_dir / "cv_features.csv"

    @property
    def features_output_path(self) -> Path:
        return self.processed_dir / "vectra_health_features.csv"

    @property
    def train_ready_output_path(self) -> Path:
        return self.processed_dir / "vectra_health_train_ready.csv"

    @property
    def feature_metadata_path(self) -> Path:
        return self.processed_dir / "feature_metadata.csv"

    def create_all(self) -> None:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.cv_processed_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Diretórios de features verificados/criados.")


# ==========================================================
# Utilitários
# ==========================================================

def read_csv(path: Path) -> pd.DataFrame:
    """Lê CSV com validação de existência."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    df = pd.read_csv(path, encoding="utf-8")
    logger.info("Arquivo carregado: %s | shape=%s", path, df.shape)
    return df


def save_csv(df: pd.DataFrame, path: Path) -> None:
    """Salva CSV em UTF-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    logger.info("Arquivo salvo: %s | shape=%s", path, df.shape)


def ensure_required_columns(df: pd.DataFrame, required_columns: Iterable[str]) -> None:
    """Valida se todas as colunas obrigatórias existem no DataFrame."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")


def sort_panel_data(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena painel município-semana."""
    df = df.copy()
    ensure_required_columns(df, ["geocode", "ano", "semana_epidemiologica"])

    df["geocode"] = df["geocode"].astype(str).str.replace(".0", "", regex=False).str.zfill(7)
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["semana_epidemiologica"] = pd.to_numeric(df["semana_epidemiologica"], errors="coerce").astype("Int64")

    df = df.dropna(subset=["geocode", "ano", "semana_epidemiologica"])
    df = df.sort_values(["geocode", "ano", "semana_epidemiologica"]).reset_index(drop=True)
    return df


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divisão segura que evita infinitos."""
    result = numerator / denominator.replace(0, np.nan)
    return result.replace([np.inf, -np.inf], np.nan)


# ==========================================================
# 1. Features epidemiológicas
# ==========================================================

def add_epidemiological_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria features baseadas na evolução temporal dos casos de dengue.

    Features criadas:
        - casos_lag_1w
        - casos_lag_2w
        - casos_lag_3w
        - casos_lag_4w
        - media_casos_2w
        - media_casos_4w
        - media_casos_8w
        - crescimento_casos_1w
        - crescimento_casos_2w
        - tendencia_casos_4w
        - incidencia_lag_1w
        - media_incidencia_4w
    """
    df = sort_panel_data(df)

    if "casos_dengue" not in df.columns:
        raise ValueError("A coluna 'casos_dengue' é obrigatória para features epidemiológicas.")

    df["casos_dengue"] = pd.to_numeric(df["casos_dengue"], errors="coerce")

    group = df.groupby("geocode", group_keys=False)

    for lag in [1, 2, 3, 4]:
        df[f"casos_lag_{lag}w"] = group["casos_dengue"].shift(lag)

    df["media_casos_2w"] = group["casos_dengue"].transform(
        lambda s: s.shift(1).rolling(window=2, min_periods=1).mean()
    )
    df["media_casos_4w"] = group["casos_dengue"].transform(
        lambda s: s.shift(1).rolling(window=4, min_periods=1).mean()
    )
    df["media_casos_8w"] = group["casos_dengue"].transform(
        lambda s: s.shift(1).rolling(window=8, min_periods=1).mean()
    )

    df["crescimento_casos_1w"] = safe_divide(
        df["casos_lag_1w"] - df["casos_lag_2w"],
        df["casos_lag_2w"].abs() + 1,
    )
    df["crescimento_casos_2w"] = safe_divide(
        df["casos_lag_1w"] - df["casos_lag_3w"],
        df["casos_lag_3w"].abs() + 1,
    )

    # Tendência simples: diferença entre média recente e média mais longa.
    df["tendencia_casos_4w"] = df["media_casos_2w"] - df["media_casos_4w"]

    if "incidencia_100k" in df.columns:
        df["incidencia_100k"] = pd.to_numeric(df["incidencia_100k"], errors="coerce")
        df["incidencia_lag_1w"] = group["incidencia_100k"].shift(1)
        df["media_incidencia_4w"] = group["incidencia_100k"].transform(
            lambda s: s.shift(1).rolling(window=4, min_periods=1).mean()
        )

    logger.info("Features epidemiológicas criadas.")
    return df


# ==========================================================
# 2. Features climáticas
# ==========================================================

def add_climate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria features climáticas temporais e anomalias.

    Features criadas quando as colunas estão disponíveis:
        - chuva_acumulada_14d
        - chuva_acumulada_21d
        - temp_media_2w
        - temp_media_4w
        - umidade_media_2w
        - umidade_media_4w
        - anomalia_temp
        - anomalia_chuva
        - condicao_vetorial_climatica
    """
    df = sort_panel_data(df)
    group = df.groupby("geocode", group_keys=False)

    climate_numeric_cols = [
        "chuva_acumulada_7d",
        "temp_media_7d",
        "temp_max_7d",
        "temp_min_7d",
        "umidade_media_7d",
        "dias_com_chuva_7d",
    ]
    for col in climate_numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "chuva_acumulada_7d" in df.columns:
        df["chuva_acumulada_14d"] = group["chuva_acumulada_7d"].transform(
            lambda s: s.shift(1).rolling(window=2, min_periods=1).sum()
        )
        df["chuva_acumulada_21d"] = group["chuva_acumulada_7d"].transform(
            lambda s: s.shift(1).rolling(window=3, min_periods=1).sum()
        )
        df["chuva_media_4w"] = group["chuva_acumulada_7d"].transform(
            lambda s: s.shift(1).rolling(window=4, min_periods=1).mean()
        )

        # Anomalia contra média histórica simplificada por município.
        historical_mean_rain = group["chuva_acumulada_7d"].transform("mean")
        historical_std_rain = group["chuva_acumulada_7d"].transform("std")
        df["anomalia_chuva"] = safe_divide(
            df["chuva_acumulada_7d"] - historical_mean_rain,
            historical_std_rain,
        )

    if "temp_media_7d" in df.columns:
        df["temp_media_2w"] = group["temp_media_7d"].transform(
            lambda s: s.shift(1).rolling(window=2, min_periods=1).mean()
        )
        df["temp_media_4w"] = group["temp_media_7d"].transform(
            lambda s: s.shift(1).rolling(window=4, min_periods=1).mean()
        )

        historical_mean_temp = group["temp_media_7d"].transform("mean")
        historical_std_temp = group["temp_media_7d"].transform("std")
        df["anomalia_temp"] = safe_divide(
            df["temp_media_7d"] - historical_mean_temp,
            historical_std_temp,
        )

    if "umidade_media_7d" in df.columns:
        df["umidade_media_2w"] = group["umidade_media_7d"].transform(
            lambda s: s.shift(1).rolling(window=2, min_periods=1).mean()
        )
        df["umidade_media_4w"] = group["umidade_media_7d"].transform(
            lambda s: s.shift(1).rolling(window=4, min_periods=1).mean()
        )

    # Índice climático heurístico para mosquito: útil como feature auxiliar.
    # Faixas gerais e simplificadas: temperatura quente + umidade + chuva recente.
    components = []

    if "temp_media_7d" in df.columns:
        temp_component = ((df["temp_media_7d"] - 18) / (32 - 18)).clip(0, 1)
        components.append(temp_component)

    if "umidade_media_7d" in df.columns:
        humidity_component = ((df["umidade_media_7d"] - 50) / (90 - 50)).clip(0, 1)
        components.append(humidity_component)

    if "chuva_acumulada_14d" in df.columns:
        rain_component = (df["chuva_acumulada_14d"] / 80).clip(0, 1)
        components.append(rain_component)

    if components:
        df["condicao_vetorial_climatica"] = pd.concat(components, axis=1).mean(axis=1)

    logger.info("Features climáticas criadas.")
    return df


# ==========================================================
# 3. Features populacionais e operacionais
# ==========================================================

def add_population_operational_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria features populacionais e proxies operacionais.

    Observação:
        Caso dados de leitos ou UBS ainda não existam, o módulo cria proxies simples
        para que a modelagem possa avançar. Quando o DataSUS/CNES for integrado,
        essas variáveis podem ser substituídas por dados reais.
    """
    df = df.copy()

    if "populacao" in df.columns:
        df["populacao"] = pd.to_numeric(df["populacao"], errors="coerce")
        df["log_populacao"] = np.log1p(df["populacao"])

    if "leitos_total" in df.columns and "populacao" in df.columns:
        df["leitos_total"] = pd.to_numeric(df["leitos_total"], errors="coerce")
        df["leitos_por_10k"] = safe_divide(df["leitos_total"], df["populacao"]) * 10_000

    # Proxy: quanto maior a incidência e menor a capacidade explícita, maior vulnerabilidade.
    # Se leitos_por_10k não existir, usa apenas incidência e população como proxy.
    if "leitos_por_10k" in df.columns and "incidencia_100k" in df.columns:
        normalized_capacity_gap = 1 - (df["leitos_por_10k"] / df["leitos_por_10k"].quantile(0.95)).clip(0, 1)
        normalized_incidence = (df["incidencia_100k"] / df["incidencia_100k"].quantile(0.95)).clip(0, 1)
        df["vulnerabilidade_operacional_proxy"] = pd.concat(
            [normalized_capacity_gap, normalized_incidence], axis=1
        ).mean(axis=1)
    elif "incidencia_100k" in df.columns:
        denominator = df["incidencia_100k"].quantile(0.95)
        if denominator and not pd.isna(denominator):
            df["vulnerabilidade_operacional_proxy"] = (df["incidencia_100k"] / denominator).clip(0, 1)
        else:
            df["vulnerabilidade_operacional_proxy"] = np.nan

    logger.info("Features populacionais e operacionais criadas.")
    return df


# ==========================================================
# 4. Integração opcional com Computer Vision
# ==========================================================

def merge_computer_vision_features(
    df: pd.DataFrame,
    cv_features_path: Path,
    region_key: str = "geocode",
) -> pd.DataFrame:
    """
    Integra features de visão computacional ao dataset principal quando disponíveis.

    O módulo de visão computacional inicial salva 'region_id'. Em produção, o ideal é
    usar region_id equivalente ao geocode municipal ou outro identificador espacial.

    Args:
        df: Dataset principal integrado.
        cv_features_path: Caminho do CSV de features CV.
        region_key: Coluna do dataset principal usada como chave espacial.

    Returns:
        DataFrame com features CV integradas, se o arquivo existir.
    """
    df = df.copy()

    if not cv_features_path.exists():
        logger.warning("Features de visão computacional não encontradas: %s", cv_features_path)
        logger.warning("Pipeline seguirá sem features CV.")
        return df

    cv_df = read_csv(cv_features_path)

    if "region_id" not in cv_df.columns:
        logger.warning("Arquivo CV não contém coluna 'region_id'. Integração ignorada.")
        return df

    cv_df = cv_df.copy()
    cv_df["region_id"] = cv_df["region_id"].astype(str).str.replace(".0", "", regex=False).str.zfill(7)

    if region_key not in df.columns:
        logger.warning("Dataset principal não contém chave %s. Integração CV ignorada.", region_key)
        return df

    df[region_key] = df[region_key].astype(str).str.replace(".0", "", regex=False).str.zfill(7)

    cv_cols = [
        "region_id",
        "water_area_pct",
        "vegetation_area_pct",
        "critical_area_pct",
        "ndvi_mean",
        "ndvi_std",
        "ndwi_mean",
        "ndwi_std",
        "ndvi_p75",
        "ndwi_p75",
    ]
    cv_cols = [col for col in cv_cols if col in cv_df.columns]

    merged = df.merge(
        cv_df[cv_cols],
        left_on=region_key,
        right_on="region_id",
        how="left",
    )

    if "region_id" in merged.columns:
        merged = merged.drop(columns=["region_id"])

    logger.info("Features de visão computacional integradas | shape=%s", merged.shape)
    return merged


# ==========================================================
# 5. Definição dos targets supervisionados
# ==========================================================

def add_supervised_targets(
    df: pd.DataFrame,
    incidence_threshold_quantile: float = 0.75,
    forecast_horizon_weeks: int = 1,
) -> pd.DataFrame:
    """
    Cria targets supervisionados para o problema de previsão de surto.

    Targets criados:
        - casos_dengue_next_1w
        - incidencia_100k_next_1w
        - target_surto_binario
        - risco_surto_multiclasse

    Args:
        df: Dataset com features.
        incidence_threshold_quantile: Percentil usado para definir surto binário.
        forecast_horizon_weeks: Horizonte de previsão em semanas.

    Returns:
        DataFrame com targets adicionados.
    """
    df = sort_panel_data(df)
    group = df.groupby("geocode", group_keys=False)

    if "casos_dengue" not in df.columns:
        raise ValueError("Coluna 'casos_dengue' é obrigatória para criar target.")

    df[f"casos_dengue_next_{forecast_horizon_weeks}w"] = group["casos_dengue"].shift(
        -forecast_horizon_weeks
    )

    if "incidencia_100k" in df.columns:
        df[f"incidencia_100k_next_{forecast_horizon_weeks}w"] = group["incidencia_100k"].shift(
            -forecast_horizon_weeks
        )
        target_base_col = f"incidencia_100k_next_{forecast_horizon_weeks}w"
    else:
        target_base_col = f"casos_dengue_next_{forecast_horizon_weeks}w"

    threshold = df[target_base_col].quantile(incidence_threshold_quantile)
    logger.info(
        "Limiar do target binário definido | coluna=%s | quantil=%.2f | threshold=%.4f",
        target_base_col,
        incidence_threshold_quantile,
        threshold,
    )

    df["target_surto_binario"] = np.where(df[target_base_col] >= threshold, 1, 0)
    df.loc[df[target_base_col].isna(), "target_surto_binario"] = np.nan

    # Target multiclasse com base em tercis/quartis da variável futura.
    q50 = df[target_base_col].quantile(0.50)
    q75 = df[target_base_col].quantile(0.75)
    q90 = df[target_base_col].quantile(0.90)

    conditions = [
        df[target_base_col].isna(),
        df[target_base_col] < q50,
        (df[target_base_col] >= q50) & (df[target_base_col] < q75),
        (df[target_base_col] >= q75) & (df[target_base_col] < q90),
        df[target_base_col] >= q90,
    ]
    choices = [np.nan, "baixo", "medio", "alto", "critico"]

    df["risco_surto_multiclasse"] = np.select(conditions, choices, default=np.nan)

    # Versão numérica para modelos que exijam target ordinal.
    risk_map = {"baixo": 0, "medio": 1, "alto": 2, "critico": 3}
    df["risco_surto_ord"] = df["risco_surto_multiclasse"].map(risk_map)

    return df


# ==========================================================
# 6. Seleção e limpeza final para modelagem
# ==========================================================

def get_feature_columns(df: pd.DataFrame) -> list[str]:
    """
    Retorna lista de colunas candidatas para modelagem.

    Remove identificadores, datas, targets e colunas textuais não modeláveis.
    """
    forbidden_prefixes = ["target_"]
    forbidden_exact = {
        "geocode",
        "municipio",
        "data_inicio_semana",
        "disease",
        "risco_surto_multiclasse",
        "risco_surto_ord",
    }
    forbidden_contains = ["next_"]

    feature_cols = []
    for col in df.columns:
        if col in forbidden_exact:
            continue
        if any(col.startswith(prefix) for prefix in forbidden_prefixes):
            continue
        if any(token in col for token in forbidden_contains):
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            feature_cols.append(col)

    return feature_cols


def build_train_ready_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cria versão final da base pronta para treino.

    Estratégia:
        - Mantém apenas linhas com target binário conhecido.
        - Mantém colunas identificadoras essenciais para auditoria.
        - Mantém features numéricas candidatas.
        - Preenche valores ausentes das features com mediana por coluna.
    """
    df = df.copy()

    if "target_surto_binario" not in df.columns:
        raise ValueError("Target 'target_surto_binario' não encontrado.")

    feature_cols = get_feature_columns(df)
    id_cols = [col for col in ["geocode", "municipio", "ano", "semana_epidemiologica"] if col in df.columns]
    target_cols = [
        "target_surto_binario",
        "risco_surto_multiclasse",
        "risco_surto_ord",
    ]
    target_cols = [col for col in target_cols if col in df.columns]

    train_ready = df[id_cols + feature_cols + target_cols].copy()
    train_ready = train_ready.dropna(subset=["target_surto_binario"])

    # Preenchimento simples e transparente para entrega acadêmica.
    for col in feature_cols:
        if train_ready[col].isna().any():
            median_value = train_ready[col].median()
            train_ready[col] = train_ready[col].fillna(median_value)

    train_ready["target_surto_binario"] = train_ready["target_surto_binario"].astype(int)

    logger.info(
        "Dataset train-ready criado | linhas=%s | features=%s",
        train_ready.shape[0],
        len(feature_cols),
    )
    return train_ready


def build_feature_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Gera metadados das features para documentação e relatório.
    """
    feature_cols = get_feature_columns(df)

    rows = []
    for col in feature_cols:
        if col.startswith("casos_") or "incidencia" in col or "media_casos" in col or "crescimento" in col:
            category = "epidemiologica"
        elif "temp" in col or "chuva" in col or "umidade" in col or "climatica" in col or "vento" in col:
            category = "climatica"
        elif "water" in col or "vegetation" in col or "ndvi" in col or "ndwi" in col or "critical" in col:
            category = "computer_vision"
        elif "populacao" in col or "leitos" in col or "vulnerabilidade" in col:
            category = "operacional_populacional"
        else:
            category = "outras"

        rows.append(
            {
                "feature": col,
                "category": category,
                "dtype": str(df[col].dtype),
                "missing_rate": float(df[col].isna().mean()),
                "mean": float(df[col].mean()) if pd.api.types.is_numeric_dtype(df[col]) else np.nan,
                "std": float(df[col].std()) if pd.api.types.is_numeric_dtype(df[col]) else np.nan,
            }
        )

    metadata = pd.DataFrame(rows)
    return metadata


# ==========================================================
# 7. Pipeline principal do Módulo 3
# ==========================================================

def run_feature_engineering_pipeline(root_dir: Path = Path(".")) -> pd.DataFrame:
    """
    Executa o pipeline completo de feature engineering.

    Args:
        root_dir: Diretório raiz do projeto.

    Returns:
        DataFrame com features completas.
    """
    paths = FeaturePaths(root_dir=root_dir)
    paths.create_all()

    logger.info("=== Carregando dataset integrado do Módulo 2 ===")
    df = read_csv(paths.input_dataset_path)
    df = sort_panel_data(df)

    logger.info("=== Criando features epidemiológicas ===")
    df = add_epidemiological_features(df)

    logger.info("=== Criando features climáticas ===")
    df = add_climate_features(df)

    logger.info("=== Criando features populacionais e operacionais ===")
    df = add_population_operational_features(df)

    logger.info("=== Integrando features de visão computacional, se existirem ===")
    df = merge_computer_vision_features(df, paths.cv_features_path)

    logger.info("=== Criando targets supervisionados ===")
    df = add_supervised_targets(
        df,
        incidence_threshold_quantile=0.75,
        forecast_horizon_weeks=1,
    )

    logger.info("=== Salvando dataset completo de features ===")
    save_csv(df, paths.features_output_path)

    logger.info("=== Criando dataset pronto para treino ===")
    train_ready = build_train_ready_dataset(df)
    save_csv(train_ready, paths.train_ready_output_path)

    logger.info("=== Gerando metadados das features ===")
    metadata = build_feature_metadata(df)
    save_csv(metadata, paths.feature_metadata_path)

    logger.info("Módulo 3 concluído com sucesso.")
    return df


if __name__ == "__main__":
    run_feature_engineering_pipeline(root_dir=Path("."))
