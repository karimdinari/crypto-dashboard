"""
Walk-Forward Backtesting Engine
================================
Implements rolling window backtest:

For each time step t:
    Train on previous TRAIN_WINDOW_SIZE days
    Predict next day
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from app.ml.direction.config import TRAIN_WINDOW_SIZE


def walk_forward_backtest(
    df: pd.DataFrame,
    feature_cols: list[str],
    model_builder,
):
    X = df[feature_cols].values
    y = df["target"].values

    total_samples = len(df)

    # Dynamically adjust training window if dataset is smaller
    train_window = min(TRAIN_WINDOW_SIZE, total_samples - 2)

    # Ensure we have enough samples
    if train_window < 200:
        raise ValueError(
            f"Not enough data for walk-forward. "
            f"Need at least 200 samples, got {total_samples}."
        )

    predictions = []
    probabilities = []
    actuals = []

    for i in range(train_window, total_samples - 1):
        X_train = X[i - train_window:i]
        y_train = y[i - train_window:i]

        X_test = X[i:i + 1]
        y_test = y[i]

        model = model_builder()
        model.fit(X_train, y_train)

        prob = model.predict_proba(X_test)[0][1]
        pred = 1 if prob >= 0.5 else 0

        probabilities.append(prob)
        predictions.append(pred)
        actuals.append(y_test)

    if len(actuals) == 0:
        raise ValueError("Walk-forward produced zero predictions.")

    acc  = accuracy_score(actuals, predictions)
    prec = precision_score(actuals, predictions)
    rec  = recall_score(actuals, predictions)
    f1   = f1_score(actuals, predictions)

    return {
        "accuracy": acc,
        "precision_up": prec,
        "recall_up": rec,
        "f1": f1,
        "predictions": predictions,
        "probabilities": probabilities,
        "actuals": actuals,
    }