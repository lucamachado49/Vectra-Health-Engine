"""Prediction utilities for trained Vectra Health models."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd


def load_trained_model(model_path: Path | str) -> Any:
    """Load a model saved with joblib."""
    return joblib.load(Path(model_path))


def predict_risk(model: Any, rows: pd.DataFrame) -> pd.DataFrame:
    """Return predicted classes and optional positive-class probabilities."""
    result = rows.copy()
    result["predicted_class"] = model.predict(rows)

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(rows)
        if proba.shape[1] > 1:
            result["probability_surto"] = proba[:, 1]

    return result


__all__ = ["load_trained_model", "predict_risk"]
