"""
Dataset Loader for BTC Direction Model
=======================================
Responsible for:
    - Loading gold/market_features parquet
    - Filtering BTC rows
    - Sorting chronologically
    - Building next-day direction target
    - Returning clean dataframe ready for feature engineering
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path

from app.ml.direction.config import SYMBOL
from app.config.settings import GOLD_PATH


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

MARKET_FEATURES_PATH = Path(GOLD_PATH) / "market_features" / "data.parquet"


# ---------------------------------------------------------------------------
# Core loader
# ---------------------------------------------------------------------------

def load_btc_dataset() -> pd.DataFrame:
    """
    Load BTC rows from gold market_features layer.

    Returns:
        DataFrame sorted by timestamp ascending.
    """
    df = pd.read_parquet(MARKET_FEATURES_PATH)

    # Filter BTC
    btc = df[df["display_symbol"] == SYMBOL].copy()

    # Sort chronologically
    btc = btc.sort_values("timestamp").reset_index(drop=True)

    return btc


# ---------------------------------------------------------------------------
# Target builder
# ---------------------------------------------------------------------------

def build_direction_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build binary direction target:
        1 → next day close higher
        0 → next day close lower or equal

    Last row dropped (no future label).

    Returns:
        DataFrame with new column 'target'
    """
    df = df.copy()

    # Future return
    df["future_return"] = df["close"].shift(-1) / df["close"] - 1

    # Binary target
    df["target"] = (df["future_return"] > 0).astype(int)

    # Drop last row (no label)
    df = df.iloc[:-1].reset_index(drop=True)

    return df