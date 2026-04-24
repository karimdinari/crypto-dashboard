"""
Feature Engineering for Direction Model
========================================
Builds ML-ready feature matrix from BTC dataset.

IMPORTANT:
All features must only use information available at time t.
No future leakage allowed.
"""

from __future__ import annotations

import pandas as pd


# ---------------------------------------------------------------------------
# Feature builder
# ---------------------------------------------------------------------------

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Derived ratios
    df["ma7_ratio"]  = df["close"] / df["ma7"]
    df["ma30_ratio"] = df["close"] / df["ma30"]

    # Momentum features
    df["momentum_3d"] = df["returns"].rolling(3).sum()
    df["momentum_7d"] = df["returns"].rolling(7).sum()

    # Volatility change
    df["volatility_change"] = df["volatility"].diff()

    # Only drop rows where OUR engineered columns are NaN
    required_cols = [
        "ma7_ratio",
        "ma30_ratio",
        "momentum_3d",
        "momentum_7d",
        "volatility_change",
    ]

    df = df.dropna(subset=required_cols).reset_index(drop=True)

    return df


# ---------------------------------------------------------------------------
# Feature selector
# ---------------------------------------------------------------------------

def select_feature_columns(df: pd.DataFrame) -> list[str]:
    exclude = {
        "symbol",
        "display_symbol",
        "market_type",
        "timestamp",
        "source",
        "ingestion_time",
        "future_return",
        "target",
    }

    return [col for col in df.columns if col not in exclude]