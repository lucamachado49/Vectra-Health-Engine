"""
Módulo 4 — Modelagem Supervisionada do Vectra Health

Caminho recomendado no projeto:
    src/models/train_models.py

Objetivo:
    Treinar, avaliar e salvar modelos supervisionados para previsão de risco de surto.

Entrada principal:
    data/processed/vectra_health_train_ready.csv

Saídas:
    models/baseline_logistic_regression.pkl
    models/random_forest_classifier.pkl
    models/xgboost_classifier.pkl  # opcional, se xgboost estiver instalado
    models/model_metrics.json
    data/processed/vectra_health_train.csv
    data/processed/vectra_health_test.csv
    reports/figures/confusion_matrix_*.png
    reports/figures/feature_importance_*.png
    reports/figures/roc_curve_*.png

Modelos:
    1. Logistic Regression — baseline interpretável.
    2. Random Forest — modelo principal robusto.
    3. XGBoost — modelo avançado opcional.

Métrica prioritária do projeto:
    Recall, porque em saúde pública é mais grave deixar de identificar uma região
    que realmente entrará em risco de surto do que gerar um falso alerta moderado.

Dependências:
    pip install pandas numpy scikit-learn matplotlib joblib
    pip install xgboost  # opcional
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    RocCurveDisplay,
    ConfusionMatrixDisplay,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBClassifier = None
    XGBOOST_AVAILABLE = False


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
class ModelPaths:
    """Centraliza os caminhos utilizados no Módulo 4."""

    root_dir: Path = Path(".")

    @property
    def processed_dir(self) -> Path:
        return self.root_dir / "data" / "processed"

    @property
    def models_dir(self) -> Path:
        return self.root_dir / "models"

    @property
    def reports_figures_dir(self) -> Path:
        return self.root_dir / "reports" / "figures"

    @property
    def input_train_ready_path(self) -> Path:
        return self.processed_dir / "vectra_health_train_ready.csv"

    @property
    def train_output_path(self) -> Path:
        return self.processed_dir / "vectra_health_train.csv"

    @property
    def test_output_path(self) -> Path:
        return self.processed_dir / "vectra_health_test.csv"

    @property
    def metrics_output_path(self) -> Path:
        return self.models_dir / "model_metrics.json"

    def create_all(self) -> None:
        for folder in [self.processed_dir, self.models_dir, self.reports_figures_dir]:
            folder.mkdir(parents=True, exist_ok=True)
            logger.info("Diretório verificado/criado: %s", folder)


# ==========================================================
# Utilitários de I/O
# ==========================================================

def read_dataset(path: Path) -> pd.DataFrame:
    """Carrega o dataset pronto para treino."""
    if not path.exists():
        raise FileNotFoundError(f"Dataset de treino não encontrado: {path}")
    df = pd.read_csv(path, encoding="utf-8")
    logger.info("Dataset carregado: %s | shape=%s", path, df.shape)
    return df


def save_dataset(df: pd.DataFrame, path: Path) -> None:
    """Salva DataFrame em CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    logger.info("Dataset salvo: %s | shape=%s", path, df.shape)


def save_json(payload: dict[str, Any], path: Path) -> None:
    """Salva dicionário em JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
    logger.info("JSON salvo: %s", path)


def save_model(model: Pipeline, path: Path) -> None:
    """Salva modelo sklearn/joblib."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    logger.info("Modelo salvo: %s", path)


# ==========================================================
# Preparação de dados
# ==========================================================

def get_identifier_columns(df: pd.DataFrame) -> list[str]:
    """Colunas mantidas para auditoria, mas não usadas como features."""
    candidates = ["geocode", "municipio", "ano", "semana_epidemiologica"]
    return [col for col in candidates if col in df.columns]


def get_target_column(df: pd.DataFrame) -> str:
    """Retorna a coluna target principal."""
    target = "target_surto_binario"
    if target not in df.columns:
        raise ValueError(f"Target obrigatório ausente: {target}")
    return target


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    """
    Seleciona colunas numéricas de features.

    Remove identificadores, targets e colunas auxiliares de classificação textual.
    """
    forbidden = set(get_identifier_columns(df)) | {
        "target_surto_binario",
        "risco_surto_multiclasse",
        "risco_surto_ord",
    }
    forbidden_tokens = ["next_"]

    feature_cols = []
    for col in df.columns:
        if col in forbidden:
            continue
        if any(token in col for token in forbidden_tokens):
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            feature_cols.append(col)

    if not feature_cols:
        raise ValueError("Nenhuma feature numérica encontrada para modelagem.")

    logger.info("Features selecionadas: %s", len(feature_cols))
    return feature_cols


def temporal_group_split(
    df: pd.DataFrame,
    test_size: float = 0.25,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Divide treino e teste preservando grupos temporais por ano-semana.

    Justificativa:
        Em séries temporais/painéis epidemiológicos, embaralhar linhas aleatoriamente
        pode gerar vazamento temporal. Aqui usamos uma divisão cronológica simples:
        semanas mais antigas para treino e semanas mais recentes para teste.

    Args:
        df: Dataset completo.
        test_size: Proporção aproximada das semanas mais recentes para teste.

    Returns:
        train_df, test_df
    """
    if "ano" not in df.columns or "semana_epidemiologica" not in df.columns:
        logger.warning("Colunas temporais ausentes. Usando GroupShuffleSplit por geocode.")
        splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=42)
        groups = df["geocode"] if "geocode" in df.columns else np.arange(len(df))
        train_idx, test_idx = next(splitter.split(df, groups=groups))
        return df.iloc[train_idx].copy(), df.iloc[test_idx].copy()

    work = df.copy()
    work["ano"] = pd.to_numeric(work["ano"], errors="coerce")
    work["semana_epidemiologica"] = pd.to_numeric(work["semana_epidemiologica"], errors="coerce")
    work = work.dropna(subset=["ano", "semana_epidemiologica"])
    work["time_key"] = work["ano"].astype(int) * 100 + work["semana_epidemiologica"].astype(int)

    unique_time_keys = sorted(work["time_key"].unique())
    if len(unique_time_keys) < 4:
        logger.warning("Poucas semanas disponíveis. Usando divisão aleatória por grupo.")
        splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=42)
        groups = work["geocode"] if "geocode" in work.columns else np.arange(len(work))
        train_idx, test_idx = next(splitter.split(work, groups=groups))
        return work.iloc[train_idx].drop(columns=["time_key"]).copy(), work.iloc[test_idx].drop(columns=["time_key"]).copy()

    split_position = int(len(unique_time_keys) * (1 - test_size))
    split_position = max(1, min(split_position, len(unique_time_keys) - 1))
    cutoff = unique_time_keys[split_position]

    train_df = work[work["time_key"] < cutoff].drop(columns=["time_key"]).copy()
    test_df = work[work["time_key"] >= cutoff].drop(columns=["time_key"]).copy()

    logger.info(
        "Divisão temporal concluída | cutoff=%s | treino=%s | teste=%s",
        cutoff,
        train_df.shape,
        test_df.shape,
    )
    return train_df, test_df


def prepare_xy(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """Separa X/y de treino e teste."""
    X_train = train_df[feature_cols].copy()
    y_train = train_df[target_col].astype(int).copy()
    X_test = test_df[feature_cols].copy()
    y_test = test_df[target_col].astype(int).copy()

    return X_train, y_train, X_test, y_test


# ==========================================================
# Construção dos modelos
# ==========================================================

def build_numeric_preprocessor(feature_cols: list[str], scale: bool = False) -> ColumnTransformer:
    """
    Cria pré-processador para features numéricas.

    Para Logistic Regression usamos escala.
    Para árvores, escala não é necessária.
    """
    steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))

    numeric_pipeline = Pipeline(steps=steps)

    return ColumnTransformer(
        transformers=[("numeric", numeric_pipeline, feature_cols)],
        remainder="drop",
    )


def build_logistic_regression_pipeline(feature_cols: list[str]) -> Pipeline:
    """Cria pipeline de Logistic Regression baseline."""
    preprocessor = build_numeric_preprocessor(feature_cols, scale=True)
    classifier = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=42,
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )


def build_random_forest_pipeline(feature_cols: list[str]) -> Pipeline:
    """Cria pipeline de Random Forest."""
    preprocessor = build_numeric_preprocessor(feature_cols, scale=False)
    classifier = RandomForestClassifier(
        n_estimators=400,
        max_depth=None,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )


def build_xgboost_pipeline(feature_cols: list[str], y_train: pd.Series) -> Optional[Pipeline]:
    """Cria pipeline XGBoost quando a biblioteca estiver disponível."""
    if not XGBOOST_AVAILABLE:
        logger.warning("xgboost não está instalado. Modelo XGBoost será ignorado.")
        return None

    preprocessor = build_numeric_preprocessor(feature_cols, scale=False)

    positive_count = int((y_train == 1).sum())
    negative_count = int((y_train == 0).sum())
    scale_pos_weight = negative_count / max(positive_count, 1)

    classifier = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="binary:logistic",
        eval_metric="logloss",
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )


# ==========================================================
# Avaliação dos modelos
# ==========================================================

def get_prediction_scores(model: Pipeline, X_test: pd.DataFrame) -> np.ndarray:
    """
    Retorna scores probabilísticos para a classe positiva.

    Usa predict_proba quando disponível; caso contrário, decision_function.
    """
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X_test)[:, 1]

    if hasattr(model, "decision_function"):
        raw_scores = model.decision_function(X_test)
        min_score = raw_scores.min()
        max_score = raw_scores.max()
        if max_score == min_score:
            return np.full_like(raw_scores, fill_value=0.5, dtype=float)
        return (raw_scores - min_score) / (max_score - min_score)

    return model.predict(X_test).astype(float)


def evaluate_model(
    model_name: str,
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, Any]:
    """Calcula métricas principais do modelo."""
    y_pred = model.predict(X_test)
    y_score = get_prediction_scores(model, X_test)

    metrics = {
        "model_name": model_name,
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": None,
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "n_test_samples": int(len(y_test)),
        "positive_rate_test": float(y_test.mean()),
    }

    if len(np.unique(y_test)) == 2:
        metrics["roc_auc"] = float(roc_auc_score(y_test, y_score))

    logger.info(
        "%s | accuracy=%.4f | precision=%.4f | recall=%.4f | f1=%.4f | roc_auc=%s",
        model_name,
        metrics["accuracy"],
        metrics["precision"],
        metrics["recall"],
        metrics["f1_score"],
        metrics["roc_auc"],
    )
    return metrics


def select_best_model(metrics_by_model: dict[str, dict[str, Any]]) -> str:
    """
    Seleciona o melhor modelo priorizando recall e depois F1-score.

    Justificativa:
        No Vectra Health, falso negativo é crítico: uma região em risco não pode
        deixar de ser sinalizada. Por isso, recall é prioridade.
    """
    ranking = sorted(
        metrics_by_model.items(),
        key=lambda item: (
            item[1].get("recall", 0),
            item[1].get("f1_score", 0),
            item[1].get("roc_auc") or 0,
        ),
        reverse=True,
    )
    best_model_name = ranking[0][0]
    logger.info("Melhor modelo selecionado: %s", best_model_name)
    return best_model_name


# ==========================================================
# Visualizações para relatório
# ==========================================================

def plot_confusion_matrix(
    model_name: str,
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    output_dir: Path,
) -> None:
    """Salva matriz de confusão em PNG."""
    output_dir.mkdir(parents=True, exist_ok=True)
    y_pred = model.predict(X_test)

    fig, ax = plt.subplots(figsize=(6, 5))
    ConfusionMatrixDisplay.from_predictions(
        y_test,
        y_pred,
        display_labels=["Sem surto", "Risco de surto"],
        cmap="Blues",
        ax=ax,
        colorbar=False,
    )
    ax.set_title(f"Matriz de Confusão — {model_name}")
    fig.tight_layout()

    output_path = output_dir / f"confusion_matrix_{model_name}.png"
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    logger.info("Matriz de confusão salva: %s", output_path)


def plot_roc_curve(
    model_name: str,
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    output_dir: Path,
) -> None:
    """Salva curva ROC em PNG quando houver duas classes no teste."""
    if len(np.unique(y_test)) < 2:
        logger.warning("Curva ROC ignorada para %s: y_test tem apenas uma classe.", model_name)
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    y_score = get_prediction_scores(model, X_test)

    fig, ax = plt.subplots(figsize=(6, 5))
    RocCurveDisplay.from_predictions(y_test, y_score, ax=ax)
    ax.set_title(f"Curva ROC — {model_name}")
    fig.tight_layout()

    output_path = output_dir / f"roc_curve_{model_name}.png"
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    logger.info("Curva ROC salva: %s", output_path)


def extract_feature_importance(
    model: Pipeline,
    feature_cols: list[str],
) -> Optional[pd.DataFrame]:
    """Extrai feature importance quando o classificador suporta esse atributo."""
    classifier = model.named_steps.get("classifier")

    if classifier is None:
        return None

    if hasattr(classifier, "feature_importances_"):
        importances = classifier.feature_importances_
    elif hasattr(classifier, "coef_"):
        importances = np.abs(classifier.coef_).ravel()
    else:
        return None

    if len(importances) != len(feature_cols):
        logger.warning("Tamanho de feature importance incompatível com feature_cols.")
        return None

    importance_df = pd.DataFrame(
        {
            "feature": feature_cols,
            "importance": importances,
        }
    ).sort_values("importance", ascending=False)

    return importance_df


def plot_feature_importance(
    model_name: str,
    model: Pipeline,
    feature_cols: list[str],
    output_dir: Path,
    top_n: int = 20,
) -> Optional[pd.DataFrame]:
    """Salva gráfico de importância de variáveis em PNG."""
    importance_df = extract_feature_importance(model, feature_cols)

    if importance_df is None or importance_df.empty:
        logger.warning("Feature importance não disponível para %s.", model_name)
        return None

    top_df = importance_df.head(top_n).sort_values("importance", ascending=True)

    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh(top_df["feature"], top_df["importance"])
    ax.set_title(f"Top {top_n} Features — {model_name}")
    ax.set_xlabel("Importância")
    fig.tight_layout()

    output_path = output_dir / f"feature_importance_{model_name}.png"
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    logger.info("Feature importance salva: %s", output_path)

    csv_path = output_dir / f"feature_importance_{model_name}.csv"
    importance_df.to_csv(csv_path, index=False, encoding="utf-8")
    logger.info("Feature importance CSV salva: %s", csv_path)

    return importance_df


def generate_model_report_figures(
    models: dict[str, Pipeline],
    X_test: pd.DataFrame,
    y_test: pd.Series,
    feature_cols: list[str],
    output_dir: Path,
) -> None:
    """Gera figuras de avaliação para todos os modelos treinados."""
    for model_name, model in models.items():
        plot_confusion_matrix(model_name, model, X_test, y_test, output_dir)
        plot_roc_curve(model_name, model, X_test, y_test, output_dir)
        plot_feature_importance(model_name, model, feature_cols, output_dir)


# ==========================================================
# Pipeline principal de modelagem
# ==========================================================

def train_and_evaluate_models(root_dir: Path = Path(".")) -> dict[str, Any]:
    """
    Executa o pipeline completo do Módulo 4.

    Args:
        root_dir: Diretório raiz do projeto.

    Returns:
        Dicionário com métricas, melhor modelo e caminhos salvos.
    """
    paths = ModelPaths(root_dir=root_dir)
    paths.create_all()

    logger.info("=== Carregando dataset train-ready ===")
    df = read_dataset(paths.input_train_ready_path)

    target_col = get_target_column(df)
    feature_cols = get_feature_columns(df)

    logger.info("=== Dividindo treino e teste ===")
    train_df, test_df = temporal_group_split(df, test_size=0.25)
    save_dataset(train_df, paths.train_output_path)
    save_dataset(test_df, paths.test_output_path)

    X_train, y_train, X_test, y_test = prepare_xy(train_df, test_df, feature_cols, target_col)

    logger.info("=== Treinando Logistic Regression baseline ===")
    logistic_model = build_logistic_regression_pipeline(feature_cols)
    logistic_model.fit(X_train, y_train)

    logger.info("=== Treinando Random Forest ===")
    random_forest_model = build_random_forest_pipeline(feature_cols)
    random_forest_model.fit(X_train, y_train)

    trained_models: dict[str, Pipeline] = {
        "logistic_regression": logistic_model,
        "random_forest": random_forest_model,
    }

    logger.info("=== Treinando XGBoost, se disponível ===")
    xgboost_model = build_xgboost_pipeline(feature_cols, y_train)
    if xgboost_model is not None:
        xgboost_model.fit(X_train, y_train)
        trained_models["xgboost"] = xgboost_model

    logger.info("=== Avaliando modelos ===")
    metrics_by_model: dict[str, dict[str, Any]] = {}
    for model_name, model in trained_models.items():
        metrics_by_model[model_name] = evaluate_model(model_name, model, X_test, y_test)

    best_model_name = select_best_model(metrics_by_model)

    logger.info("=== Salvando modelos ===")
    save_model(logistic_model, paths.models_dir / "baseline_logistic_regression.pkl")
    save_model(random_forest_model, paths.models_dir / "random_forest_classifier.pkl")
    if "xgboost" in trained_models:
        save_model(trained_models["xgboost"], paths.models_dir / "xgboost_classifier.pkl")

    # Salva também uma cópia padronizada do melhor modelo.
    save_model(trained_models[best_model_name], paths.models_dir / "best_model.pkl")

    logger.info("=== Gerando figuras para relatório ===")
    generate_model_report_figures(
        models=trained_models,
        X_test=X_test,
        y_test=y_test,
        feature_cols=feature_cols,
        output_dir=paths.reports_figures_dir,
    )

    result = {
        "target_col": target_col,
        "feature_count": len(feature_cols),
        "feature_cols": feature_cols,
        "train_shape": list(train_df.shape),
        "test_shape": list(test_df.shape),
        "best_model_name": best_model_name,
        "metrics_by_model": metrics_by_model,
        "model_paths": {
            "logistic_regression": str(paths.models_dir / "baseline_logistic_regression.pkl"),
            "random_forest": str(paths.models_dir / "random_forest_classifier.pkl"),
            "xgboost": str(paths.models_dir / "xgboost_classifier.pkl") if "xgboost" in trained_models else None,
            "best_model": str(paths.models_dir / "best_model.pkl"),
        },
        "priority_metric": "recall",
        "priority_metric_reason": (
            "Em vigilância epidemiológica, falso negativo é crítico: "
            "uma região em risco não deve deixar de ser sinalizada."
        ),
    }

    save_json(result, paths.metrics_output_path)

    logger.info("Módulo 4 concluído com sucesso.")
    return result


if __name__ == "__main__":
    train_and_evaluate_models(root_dir=Path("."))
