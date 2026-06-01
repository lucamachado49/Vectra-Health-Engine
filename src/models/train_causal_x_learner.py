"""Causal X-Learner prototype for preventive intervention impact.

The predictive model estimates outbreak risk. This module estimates the
counterfactual impact of an intervention, for example early field action,
SMS alerts, UBS reinforcement, or sanitation response.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split


@dataclass
class XLearnerResult:
    cate: np.ndarray
    ate: float
    mae_treated: float
    mae_control: float


class VectraXLearner:
    """Minimal X-Learner using sklearn estimators.

    treatment_col should identify municipalities/weeks that received a
    preventive action. outcome_col can be next-week incidence or binary
    outbreak risk. The output is the estimated individual treatment effect.
    """

    def __init__(self) -> None:
        self.mu0 = RandomForestRegressor(n_estimators=250, random_state=42, min_samples_leaf=4)
        self.mu1 = RandomForestRegressor(n_estimators=250, random_state=43, min_samples_leaf=4)
        self.tau0 = RandomForestRegressor(n_estimators=250, random_state=44, min_samples_leaf=4)
        self.tau1 = RandomForestRegressor(n_estimators=250, random_state=45, min_samples_leaf=4)
        self.propensity: float = 0.5

    def fit(self, X: pd.DataFrame, treatment: pd.Series, outcome: pd.Series) -> "VectraXLearner":
        treated = treatment.astype(int) == 1
        control = ~treated
        if treated.sum() < 10 or control.sum() < 10:
            raise ValueError("X-Learner needs treated and control samples.")

        self.propensity = float(treated.mean())
        self.mu1.fit(X.loc[treated], outcome.loc[treated])
        self.mu0.fit(X.loc[control], outcome.loc[control])

        d1 = outcome.loc[treated] - self.mu0.predict(X.loc[treated])
        d0 = self.mu1.predict(X.loc[control]) - outcome.loc[control]
        self.tau1.fit(X.loc[treated], d1)
        self.tau0.fit(X.loc[control], d0)
        return self

    def predict_cate(self, X: pd.DataFrame) -> np.ndarray:
        tau_control = self.tau0.predict(X)
        tau_treated = self.tau1.predict(X)
        return self.propensity * tau_control + (1 - self.propensity) * tau_treated


def train_x_learner(
    df: pd.DataFrame,
    feature_cols: list[str],
    treatment_col: str = "intervencao_preventiva",
    outcome_col: str = "target_surto_binario",
) -> XLearnerResult:
    """Train and evaluate the causal learner on tabular weekly data."""
    work = df.dropna(subset=feature_cols + [treatment_col, outcome_col]).copy()
    train, test = train_test_split(work, test_size=0.25, random_state=42, stratify=work[treatment_col])

    learner = VectraXLearner().fit(
        train[feature_cols],
        train[treatment_col],
        train[outcome_col],
    )
    cate = learner.predict_cate(test[feature_cols])

    treated = test[treatment_col].astype(int) == 1
    mae_treated = mean_absolute_error(test.loc[treated, outcome_col], learner.mu1.predict(test.loc[treated, feature_cols]))
    mae_control = mean_absolute_error(test.loc[~treated, outcome_col], learner.mu0.predict(test.loc[~treated, feature_cols]))
    return XLearnerResult(cate=cate, ate=float(np.mean(cate)), mae_treated=mae_treated, mae_control=mae_control)
