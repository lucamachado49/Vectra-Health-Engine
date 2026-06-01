"""
Módulo 5 — Visualização e Explicabilidade do Vectra Health

Caminho recomendado no projeto:
    src/visualization/generate_reports.py

Objetivo:
    Gerar visualizações consolidadas e artefatos explicáveis para o PDF, pitch,
    notebook final e dashboard do Vectra Health.

Entradas esperadas:
    data/processed/vectra_health_features.csv
    data/processed/vectra_health_train_ready.csv
    data/processed/vectra_health_latest_risk_snapshot.csv
    models/model_metrics.json
    reports/figures/feature_importance_random_forest.csv  # se existir
    reports/figures/feature_importance_xgboost.csv        # se existir

Saídas principais:
    reports/figures/model_comparison.png
    reports/figures/target_distribution.png
    reports/figures/risk_distribution.png
    reports/figures/top_features_overall.png
    reports/figures/cases_over_time.png
    reports/figures/climate_vs_cases.png
    reports/figures/environmental_risk_distribution.png
    reports/figures/latest_risk_ranking.png
    reports/tables/model_comparison.csv
    reports/tables/latest_risk_ranking.csv
    reports/summary/modeling_summary.md

Dependências:
    pip install pandas numpy matplotlib

Observação:
    Este módulo não treina modelos. Ele consome os resultados dos Módulos 3 e 4.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import matplotlib.pyplot as plt
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
class VisualizationPaths:
    """Centraliza caminhos usados pelo Módulo 5."""

    root_dir: Path = Path(".")

    @property
    def processed_dir(self) -> Path:
        return self.root_dir / "data" / "processed"

    @property
    def models_dir(self) -> Path:
        return self.root_dir / "models"

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

    @property
    def features_path(self) -> Path:
        return self.processed_dir / "vectra_health_features.csv"

    @property
    def train_ready_path(self) -> Path:
        return self.processed_dir / "vectra_health_train_ready.csv"

    @property
    def latest_risk_path(self) -> Path:
        return self.processed_dir / "vectra_health_latest_risk_snapshot.csv"

    @property
    def metrics_path(self) -> Path:
        return self.models_dir / "model_metrics.json"

    def create_all(self) -> None:
        for folder in [self.figures_dir, self.tables_dir, self.summary_dir]:
            folder.mkdir(parents=True, exist_ok=True)
            logger.info("Diretório verificado/criado: %s", folder)


# ==========================================================
# Utilitários de I/O
# ==========================================================

def read_csv_if_exists(path: Path) -> Optional[pd.DataFrame]:
    """Lê CSV se existir; caso contrário, retorna None."""
    if not path.exists():
        logger.warning("Arquivo não encontrado: %s", path)
        return None
    df = pd.read_csv(path, encoding="utf-8")
    logger.info("CSV carregado: %s | shape=%s", path, df.shape)
    return df


def read_json_if_exists(path: Path) -> Optional[dict[str, Any]]:
    """Lê JSON se existir; caso contrário, retorna None."""
    if not path.exists():
        logger.warning("JSON não encontrado: %s", path)
        return None
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    logger.info("JSON carregado: %s", path)
    return payload


def save_table(df: pd.DataFrame, path: Path) -> None:
    """Salva tabela CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    logger.info("Tabela salva: %s | shape=%s", path, df.shape)


def save_markdown(text: str, path: Path) -> None:
    """Salva texto markdown."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    logger.info("Markdown salvo: %s", path)


def save_current_figure(path: Path, dpi: int = 180) -> None:
    """Salva a figura atual com layout ajustado."""
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close()
    logger.info("Figura salva: %s", path)


def format_pct(value: float) -> str:
    """Formata decimal como percentual."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value * 100:.1f}%"


# ==========================================================
# 1. Métricas e comparação de modelos
# ==========================================================

def metrics_json_to_dataframe(metrics_payload: dict[str, Any]) -> pd.DataFrame:
    """
    Converte o JSON de métricas do Módulo 4 em DataFrame tabular.
    """
    metrics_by_model = metrics_payload.get("metrics_by_model", {})
    rows = []

    for model_name, metrics in metrics_by_model.items():
        rows.append(
            {
                "model_name": model_name,
                "accuracy": metrics.get("accuracy"),
                "precision": metrics.get("precision"),
                "recall": metrics.get("recall"),
                "f1_score": metrics.get("f1_score"),
                "roc_auc": metrics.get("roc_auc"),
                "positive_rate_test": metrics.get("positive_rate_test"),
                "n_test_samples": metrics.get("n_test_samples"),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["recall", "f1_score", "roc_auc"], ascending=False).reset_index(drop=True)

    return df


def plot_model_comparison(metrics_df: pd.DataFrame, output_path: Path) -> None:
    """
    Gera gráfico comparando Accuracy, Precision, Recall, F1 e ROC-AUC.
    """
    if metrics_df.empty:
        logger.warning("metrics_df vazio. Comparação de modelos ignorada.")
        return

    plot_df = metrics_df.set_index("model_name")[["accuracy", "precision", "recall", "f1_score", "roc_auc"]]
    plot_df = plot_df.fillna(0)

    ax = plot_df.plot(kind="bar", figsize=(10, 6))
    ax.set_title("Comparação de Performance dos Modelos")
    ax.set_xlabel("Modelo")
    ax.set_ylabel("Pontuação")
    ax.set_ylim(0, 1)
    ax.legend(title="Métrica", loc="lower right")
    ax.grid(axis="y", alpha=0.3)

    save_current_figure(output_path)


# ==========================================================
# 2. Distribuição do target e risco
# ==========================================================

def plot_target_distribution(train_ready_df: pd.DataFrame, output_path: Path) -> None:
    """Gera gráfico de distribuição do target binário."""
    if "target_surto_binario" not in train_ready_df.columns:
        logger.warning("target_surto_binario ausente. Gráfico ignorado.")
        return

    counts = train_ready_df["target_surto_binario"].value_counts(dropna=False).sort_index()
    labels = ["Sem surto", "Risco de surto"]

    plt.figure(figsize=(7, 5))
    plt.bar(labels[: len(counts)], counts.values)
    plt.title("Distribuição do Target Binário")
    plt.ylabel("Número de observações")
    plt.xlabel("Classe")
    plt.grid(axis="y", alpha=0.3)

    for idx, value in enumerate(counts.values):
        plt.text(idx, value, str(value), ha="center", va="bottom")

    save_current_figure(output_path)


def plot_risk_multiclass_distribution(features_df: pd.DataFrame, output_path: Path) -> None:
    """Gera distribuição do risco multiclasse."""
    if "risco_surto_multiclasse" not in features_df.columns:
        logger.warning("risco_surto_multiclasse ausente. Gráfico ignorado.")
        return

    order = ["baixo", "medio", "alto", "critico"]
    counts = features_df["risco_surto_multiclasse"].value_counts().reindex(order).fillna(0)

    plt.figure(figsize=(8, 5))
    plt.bar(counts.index, counts.values)
    plt.title("Distribuição do Risco de Surto por Classe")
    plt.ylabel("Número de observações")
    plt.xlabel("Classe de risco")
    plt.grid(axis="y", alpha=0.3)

    for idx, value in enumerate(counts.values):
        plt.text(idx, value, str(int(value)), ha="center", va="bottom")

    save_current_figure(output_path)


# ==========================================================
# 3. Feature importance consolidada
# ==========================================================

def load_available_feature_importances(figures_dir: Path) -> pd.DataFrame:
    """
    Carrega arquivos CSV de feature importance gerados no Módulo 4.
    """
    files = sorted(figures_dir.glob("feature_importance_*.csv"))
    frames = []

    for path in files:
        df = pd.read_csv(path, encoding="utf-8")
        model_name = path.stem.replace("feature_importance_", "")
        df["model_name"] = model_name
        frames.append(df)

    if not frames:
        logger.warning("Nenhum CSV de feature importance encontrado em %s", figures_dir)
        return pd.DataFrame()

    result = pd.concat(frames, ignore_index=True)
    logger.info("Feature importances carregadas | shape=%s", result.shape)
    return result


def build_overall_feature_importance(importance_df: pd.DataFrame) -> pd.DataFrame:
    """
    Consolida importância média das features entre modelos disponíveis.
    """
    if importance_df.empty:
        return importance_df

    # Normaliza importância dentro de cada modelo para comparabilidade aproximada.
    work = importance_df.copy()
    work["importance"] = pd.to_numeric(work["importance"], errors="coerce").fillna(0)
    work["importance_norm"] = work.groupby("model_name")["importance"].transform(
        lambda s: s / s.sum() if s.sum() > 0 else s
    )

    overall = (
        work.groupby("feature", as_index=False)
        .agg(
            importance_mean=("importance_norm", "mean"),
            importance_max=("importance_norm", "max"),
            models_count=("model_name", "nunique"),
        )
        .sort_values("importance_mean", ascending=False)
        .reset_index(drop=True)
    )

    return overall


def plot_top_features(overall_importance: pd.DataFrame, output_path: Path, top_n: int = 20) -> None:
    """Gera gráfico consolidado das features mais importantes."""
    if overall_importance.empty:
        logger.warning("overall_importance vazio. Gráfico de features ignorado.")
        return

    top = overall_importance.head(top_n).sort_values("importance_mean", ascending=True)

    plt.figure(figsize=(9, 7))
    plt.barh(top["feature"], top["importance_mean"])
    plt.title(f"Top {top_n} Variáveis Mais Importantes")
    plt.xlabel("Importância média normalizada")
    plt.ylabel("Feature")
    plt.grid(axis="x", alpha=0.3)

    save_current_figure(output_path)


# ==========================================================
# 4. Séries temporais epidemiológicas e climáticas
# ==========================================================

def build_time_label(df: pd.DataFrame) -> pd.Series:
    """Cria rótulo temporal ano-semana para gráficos."""
    return df["ano"].astype(str) + "-W" + df["semana_epidemiologica"].astype(str).str.zfill(2)


def plot_cases_over_time(features_df: pd.DataFrame, output_path: Path) -> None:
    """Gera série temporal agregada de casos de dengue."""
    required = ["ano", "semana_epidemiologica", "casos_dengue"]
    if any(col not in features_df.columns for col in required):
        logger.warning("Colunas insuficientes para casos ao longo do tempo.")
        return

    work = features_df.copy()
    work["time_key"] = work["ano"].astype(int) * 100 + work["semana_epidemiologica"].astype(int)
    weekly = (
        work.groupby(["time_key", "ano", "semana_epidemiologica"], as_index=False)["casos_dengue"]
        .sum()
        .sort_values("time_key")
    )
    weekly["time_label"] = build_time_label(weekly)

    plt.figure(figsize=(12, 5))
    plt.plot(weekly["time_label"], weekly["casos_dengue"], marker="o", markersize=2)
    plt.title("Evolução Semanal de Casos de Dengue")
    plt.xlabel("Semana epidemiológica")
    plt.ylabel("Casos agregados")
    plt.grid(alpha=0.3)
    plt.xticks(rotation=90)

    # Reduz quantidade de rótulos no eixo X.
    ax = plt.gca()
    ticks = ax.get_xticks()
    step = max(1, len(ticks) // 15)
    ax.set_xticks(ticks[::step])

    save_current_figure(output_path)


def plot_climate_vs_cases(features_df: pd.DataFrame, output_path: Path) -> None:
    """
    Gera gráfico comparando casos, chuva e temperatura média ao longo do tempo.
    """
    required = ["ano", "semana_epidemiologica", "casos_dengue"]
    if any(col not in features_df.columns for col in required):
        logger.warning("Colunas insuficientes para clima vs casos.")
        return

    climate_cols = [col for col in ["chuva_acumulada_7d", "temp_media_7d"] if col in features_df.columns]
    if not climate_cols:
        logger.warning("Nenhuma coluna climática disponível para clima vs casos.")
        return

    work = features_df.copy()
    work["time_key"] = work["ano"].astype(int) * 100 + work["semana_epidemiologica"].astype(int)

    aggregation = {"casos_dengue": "sum"}
    for col in climate_cols:
        aggregation[col] = "mean"

    weekly = (
        work.groupby(["time_key", "ano", "semana_epidemiologica"], as_index=False)
        .agg(aggregation)
        .sort_values("time_key")
    )
    weekly["time_label"] = build_time_label(weekly)

    plt.figure(figsize=(12, 5))
    plt.plot(weekly["time_label"], normalize_series(weekly["casos_dengue"]), label="Casos dengue normalizados")

    if "chuva_acumulada_7d" in weekly.columns:
        plt.plot(weekly["time_label"], normalize_series(weekly["chuva_acumulada_7d"]), label="Chuva normalizada")

    if "temp_media_7d" in weekly.columns:
        plt.plot(weekly["time_label"], normalize_series(weekly["temp_media_7d"]), label="Temperatura normalizada")

    plt.title("Relação Temporal entre Clima e Casos de Dengue")
    plt.xlabel("Semana epidemiológica")
    plt.ylabel("Valor normalizado 0-1")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.xticks(rotation=90)

    ax = plt.gca()
    ticks = ax.get_xticks()
    step = max(1, len(ticks) // 15)
    ax.set_xticks(ticks[::step])

    save_current_figure(output_path)


def normalize_series(series: pd.Series) -> pd.Series:
    """Normaliza uma série entre 0 e 1."""
    series = pd.to_numeric(series, errors="coerce")
    min_value = series.min()
    max_value = series.max()
    if pd.isna(min_value) or pd.isna(max_value) or max_value == min_value:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - min_value) / (max_value - min_value)


# ==========================================================
# 5. Snapshot de risco e ranking operacional
# ==========================================================

def build_latest_risk_ranking(latest_df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """
    Cria ranking operacional das regiões mais críticas no snapshot mais recente.
    """
    if latest_df is None or latest_df.empty:
        return pd.DataFrame()

    work = latest_df.copy()

    ranking_cols = [
        "geocode",
        "municipio",
        "ano",
        "semana_epidemiologica",
        "casos_dengue",
        "incidencia_100k",
        "environmental_risk_score",
        "risco_ambiental_label",
        "temp_media_7d",
        "chuva_acumulada_7d",
        "umidade_media_7d",
    ]
    ranking_cols = [col for col in ranking_cols if col in work.columns]

    sort_cols = [col for col in ["environmental_risk_score", "incidencia_100k", "casos_dengue"] if col in work.columns]
    if sort_cols:
        work = work.sort_values(sort_cols, ascending=False)

    return work[ranking_cols].head(top_n).reset_index(drop=True)


def plot_latest_risk_ranking(ranking_df: pd.DataFrame, output_path: Path) -> None:
    """Gera gráfico do ranking mais recente de risco ambiental/epidemiológico."""
    if ranking_df.empty:
        logger.warning("Ranking vazio. Gráfico de ranking ignorado.")
        return

    if "municipio" not in ranking_df.columns or "environmental_risk_score" not in ranking_df.columns:
        logger.warning("Ranking sem colunas necessárias para gráfico.")
        return

    plot_df = ranking_df.sort_values("environmental_risk_score", ascending=True)

    plt.figure(figsize=(9, 7))
    plt.barh(plot_df["municipio"], plot_df["environmental_risk_score"])
    plt.title("Ranking Operacional — Maiores Scores Ambientais")
    plt.xlabel("Environmental Risk Score")
    plt.ylabel("Município")
    plt.grid(axis="x", alpha=0.3)

    save_current_figure(output_path)


def plot_environmental_risk_distribution(features_df: pd.DataFrame, output_path: Path) -> None:
    """Gera histograma do environmental_risk_score."""
    if "environmental_risk_score" not in features_df.columns:
        logger.warning("environmental_risk_score ausente. Histograma ignorado.")
        return

    values = pd.to_numeric(features_df["environmental_risk_score"], errors="coerce").dropna()
    if values.empty:
        logger.warning("environmental_risk_score sem valores válidos.")
        return

    plt.figure(figsize=(8, 5))
    plt.hist(values, bins=20)
    plt.title("Distribuição do Score Ambiental")
    plt.xlabel("Environmental Risk Score")
    plt.ylabel("Frequência")
    plt.grid(axis="y", alpha=0.3)

    save_current_figure(output_path)


# ==========================================================
# 6. Sumário executivo em Markdown
# ==========================================================

def build_modeling_summary(
    metrics_df: pd.DataFrame,
    metrics_payload: Optional[dict[str, Any]],
    latest_ranking: pd.DataFrame,
    overall_importance: pd.DataFrame,
) -> str:
    """
    Gera sumário textual para relatório/pitch.
    """
    if metrics_df.empty:
        best_line = "Não foi possível identificar o melhor modelo porque as métricas não foram encontradas."
    else:
        best = metrics_df.iloc[0]
        best_line = (
            f"O melhor modelo segundo a estratégia de priorização por recall foi "
            f"**{best['model_name']}**, com recall de **{format_pct(best['recall'])}**, "
            f"F1-score de **{format_pct(best['f1_score'])}** e ROC-AUC de "
            f"**{format_pct(best['roc_auc']) if pd.notna(best['roc_auc']) else 'N/A'}**."
        )

    priority_reason = ""
    if metrics_payload:
        priority_reason = metrics_payload.get(
            "priority_metric_reason",
            "Recall foi priorizado por reduzir falsos negativos em contexto epidemiológico.",
        )

    top_features_text = ""
    if not overall_importance.empty:
        top_features = overall_importance.head(5)["feature"].tolist()
        top_features_text = ", ".join(top_features)
    else:
        top_features_text = "não disponível"

    top_regions_text = ""
    if not latest_ranking.empty and "municipio" in latest_ranking.columns:
        top_regions = latest_ranking.head(5)["municipio"].astype(str).tolist()
        top_regions_text = ", ".join(top_regions)
    else:
        top_regions_text = "não disponível"

    text = f"""# Sumário de Modelagem e Explicabilidade — Vectra Health

## Desempenho dos modelos

{best_line}

A métrica prioritária do projeto é **Recall**. {priority_reason}

## Variáveis mais relevantes

As principais variáveis explicativas identificadas na consolidação das importâncias foram: **{top_features_text}**.

Essas variáveis ajudam a traduzir o risco epidemiológico em fatores compreensíveis para gestores públicos, como evolução recente dos casos, chuva acumulada, temperatura, umidade e indicadores ambientais.

## Regiões prioritárias no snapshot mais recente

As regiões com maior prioridade operacional no snapshot atual foram: **{top_regions_text}**.

Essas regiões devem ser analisadas pelo painel de decisão do Vectra Health para definição de ações preventivas, como reforço de UBS, comunicação com agentes comunitários e preparação de estoque de insumos.

## Interpretação para o pitch

O Vectra Health não apenas prevê risco de surto. Ele explica quais fatores estão elevando o risco e transforma esses sinais em recomendações práticas para tomada de decisão preventiva. Isso conecta dados espaciais, epidemiologia, machine learning e gestão pública em uma solução única.
"""
    return text


# ==========================================================
# 7. Pipeline principal do Módulo 5
# ==========================================================

def run_visualization_pipeline(root_dir: Path = Path(".")) -> dict[str, Any]:
    """
    Executa o pipeline completo de visualização e explicabilidade.

    Args:
        root_dir: Diretório raiz do projeto.

    Returns:
        Dicionário com caminhos dos principais artefatos gerados.
    """
    paths = VisualizationPaths(root_dir=root_dir)
    paths.create_all()

    logger.info("=== Carregando entradas do Módulo 5 ===")
    features_df = read_csv_if_exists(paths.features_path)
    train_ready_df = read_csv_if_exists(paths.train_ready_path)
    latest_df = read_csv_if_exists(paths.latest_risk_path)
    metrics_payload = read_json_if_exists(paths.metrics_path)

    artifacts: dict[str, Any] = {
        "figures": [],
        "tables": [],
        "summaries": [],
    }

    logger.info("=== Processando métricas dos modelos ===")
    if metrics_payload:
        metrics_df = metrics_json_to_dataframe(metrics_payload)
        metrics_table_path = paths.tables_dir / "model_comparison.csv"
        save_table(metrics_df, metrics_table_path)
        artifacts["tables"].append(str(metrics_table_path))

        model_comparison_path = paths.figures_dir / "model_comparison.png"
        plot_model_comparison(metrics_df, model_comparison_path)
        artifacts["figures"].append(str(model_comparison_path))
    else:
        metrics_df = pd.DataFrame()

    logger.info("=== Gerando gráficos de target e risco ===")
    if train_ready_df is not None:
        target_distribution_path = paths.figures_dir / "target_distribution.png"
        plot_target_distribution(train_ready_df, target_distribution_path)
        artifacts["figures"].append(str(target_distribution_path))

    if features_df is not None:
        risk_distribution_path = paths.figures_dir / "risk_distribution.png"
        plot_risk_multiclass_distribution(features_df, risk_distribution_path)
        artifacts["figures"].append(str(risk_distribution_path))

        cases_over_time_path = paths.figures_dir / "cases_over_time.png"
        plot_cases_over_time(features_df, cases_over_time_path)
        artifacts["figures"].append(str(cases_over_time_path))

        climate_vs_cases_path = paths.figures_dir / "climate_vs_cases.png"
        plot_climate_vs_cases(features_df, climate_vs_cases_path)
        artifacts["figures"].append(str(climate_vs_cases_path))

        environmental_distribution_path = paths.figures_dir / "environmental_risk_distribution.png"
        plot_environmental_risk_distribution(features_df, environmental_distribution_path)
        artifacts["figures"].append(str(environmental_distribution_path))

    logger.info("=== Consolidando feature importance ===")
    raw_importance = load_available_feature_importances(paths.figures_dir)
    overall_importance = build_overall_feature_importance(raw_importance)

    if not overall_importance.empty:
        importance_table_path = paths.tables_dir / "overall_feature_importance.csv"
        save_table(overall_importance, importance_table_path)
        artifacts["tables"].append(str(importance_table_path))

        top_features_path = paths.figures_dir / "top_features_overall.png"
        plot_top_features(overall_importance, top_features_path)
        artifacts["figures"].append(str(top_features_path))

    logger.info("=== Gerando ranking operacional mais recente ===")
    if latest_df is not None:
        latest_ranking = build_latest_risk_ranking(latest_df, top_n=15)
        latest_ranking_table_path = paths.tables_dir / "latest_risk_ranking.csv"
        save_table(latest_ranking, latest_ranking_table_path)
        artifacts["tables"].append(str(latest_ranking_table_path))

        latest_ranking_path = paths.figures_dir / "latest_risk_ranking.png"
        plot_latest_risk_ranking(latest_ranking, latest_ranking_path)
        artifacts["figures"].append(str(latest_ranking_path))
    else:
        latest_ranking = pd.DataFrame()

    logger.info("=== Gerando sumário executivo ===")
    summary_text = build_modeling_summary(
        metrics_df=metrics_df,
        metrics_payload=metrics_payload,
        latest_ranking=latest_ranking,
        overall_importance=overall_importance,
    )
    summary_path = paths.summary_dir / "modeling_summary.md"
    save_markdown(summary_text, summary_path)
    artifacts["summaries"].append(str(summary_path))

    logger.info("Módulo 5 concluído com sucesso.")
    return artifacts


if __name__ == "__main__":
    run_visualization_pipeline(root_dir=Path("."))
