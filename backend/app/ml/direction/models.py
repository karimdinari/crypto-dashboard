"""
Model Wrappers for BTC Direction Prediction
============================================
Provides unified interface for:
    - Logistic Regression
    - Random Forest
    - XGBoost

All models expose:
    fit(X, y)
    predict_proba(X)
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from xgboost import XGBClassifier

from app.ml.direction.config import RANDOM_STATE


# ---------------------------------------------------------------------------
# Logistic Regression
# ---------------------------------------------------------------------------

def build_logistic_model():
    """
    Logistic Regression with scaling.
    Scaling is required because LR is sensitive to feature magnitude.
    """
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                max_iter=1000,
                random_state=RANDOM_STATE,
            )),
        ]
    )
    return model


# ---------------------------------------------------------------------------
# Random Forest
# ---------------------------------------------------------------------------

def build_random_forest():
    return RandomForestClassifier(
        n_estimators=400,
        max_depth=5,
        min_samples_split=8,
        min_samples_leaf=3,
        max_features="sqrt",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )


# ---------------------------------------------------------------------------
# XGBoost
# ---------------------------------------------------------------------------

def build_xgboost():
    return XGBClassifier(
        n_estimators=300,
        learning_rate=0.04,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        random_state=RANDOM_STATE,
        eval_metric="logloss",
        n_jobs=-1,
    )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_model(model_name: str):
    if model_name == "logistic":
        return build_logistic_model()
    elif model_name == "random_forest":
        return build_random_forest()
    elif model_name == "xgboost":
        return build_xgboost()
    else:
        raise ValueError(f"Unknown model: {model_name}")