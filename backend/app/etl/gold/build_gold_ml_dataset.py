"""
Gold ML Dataset Builder
========================
Joins the Gold market features and Gold news aggregates to produce
a unified, ML-ready parquet at:
    lakehouse/gold/ml_dataset/data.parquet

Each row = one (symbol, day) observation with:
  - OHLCV + all technical indicators (from market_features)
  - Sentiment aggregates + derived news features (from news_aggregates)

Usage:
    python -m app.etl.gold.build_gold_ml_dataset

Or import:
    from app.etl.gold.build_gold_ml_dataset import build_gold_ml_dataset
    df = build_gold_ml_dataset()
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np

from app.config.logging_config import get_logger
from app.etl.gold.schema_gold import GOLD_ML_DATASET_COLUMNS
from app.features.news_features import build_news_features, NEWS_FEATURE_COLUMNS

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

GOLD_MARKET_FILE  = "lakehouse/gold/market_features/data.parquet"
GOLD_NEWS_FILE    = "lakehouse/gold/news_aggregates/data.parquet"
GOLD_ML_DIR       = "lakehouse/gold/ml_dataset"
GOLD_ML_FILE      = "lakehouse/gold/ml_dataset/data.parquet"


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_gold_ml_dataset() -> pd.DataFrame:
    """
    Join market features + enriched news aggregates into a unified ML dataset.

    Returns:
        DataFrame with all market + news features aligned per (symbol, day).
    """
    # ---- Load market features -------------------------------------------
    if not Path(GOLD_MARKET_FILE).exists():
        raise FileNotFoundError(
            f"Market features not found: {GOLD_MARKET_FILE}\n"
            "Run: python -m app.etl.gold.build_gold_market"
        )

    logger.info("Loading Gold market features")
    market_df = pd.read_parquet(GOLD_MARKET_FILE)
    market_df["timestamp"] = pd.to_datetime(
        market_df["timestamp"], errors="coerce", utc=True
    )
    # tz-naive date key — convert UTC→naive then floor to day
    market_df["date"] = market_df["timestamp"].dt.tz_convert(None).dt.normalize()

    # ---- Load news aggregates -------------------------------------------
    news_available = Path(GOLD_NEWS_FILE).exists()
    if not news_available:
        logger.warning(
            "Gold news aggregates not found — ML dataset will have zero news features. "
            "Run: python -m app.etl.gold.build_gold_news"
        )
        news_df = pd.DataFrame()
    else:
        logger.info("Loading Gold news aggregates")
        news_df = pd.read_parquet(GOLD_NEWS_FILE)
        # Ensure tz-naive date so the join key matches market_df["date"]
        raw_date = pd.to_datetime(news_df["date"], errors="coerce", utc=True)
        news_df["date"] = raw_date.dt.tz_convert(None).dt.normalize()

    # ---- Enrich news with derived features ------------------------------
    if not news_df.empty:
        logger.info("Building derived news features")
        news_df = build_news_features(news_df, market_df=market_df)

    # ---- Join ---------------------------------------------------------
    logger.info("Joining market + news on (symbol, date)")
    if not news_df.empty:
        news_cols = [
            "symbol", "date",
            "news_count",
            "sentiment_score", "sentiment_positive",
            "sentiment_negative", "sentiment_neutral",
            "sentiment_std", "sentiment_max", "sentiment_min",
        ] + NEWS_FEATURE_COLUMNS

        news_cols = [c for c in news_cols if c in news_df.columns]
        ml_df = market_df.merge(
            news_df[news_cols],
            on=["symbol", "date"],
            how="left",
        )
    else:
        ml_df = market_df.copy()

    # ---- Fill missing news features with neutral defaults ---------------
    news_fill_defaults: dict[str, float] = {
        "news_count":          0.0,
        "sentiment_score":     0.0,
        "sentiment_positive":  0.0,
        "sentiment_negative":  0.0,
        "sentiment_neutral":   1.0,
        "sentiment_std":       0.0,
        "sentiment_max":       0.0,
        "sentiment_min":       0.0,
    }
    for col in NEWS_FEATURE_COLUMNS:
        news_fill_defaults[col] = 0.0

    for col, default in news_fill_defaults.items():
        if col not in ml_df.columns:
            ml_df[col] = default
        else:
            ml_df[col] = ml_df[col].fillna(default)

    # ---- Clean up -------------------------------------------------------
    ml_df = ml_df.replace([np.inf, -np.inf], 0.0)
    ml_df = ml_df.sort_values(["symbol", "timestamp"]).reset_index(drop=True)

    # Keep only schema columns that exist
    keep = [c for c in GOLD_ML_DATASET_COLUMNS if c in ml_df.columns]
    ml_df = ml_df[keep]

    # ---- Save -----------------------------------------------------------
    Path(GOLD_ML_DIR).mkdir(parents=True, exist_ok=True)
    ml_df.to_parquet(GOLD_ML_FILE, index=False)

    logger.info(
        "Gold ML dataset written",
        extra={"path": GOLD_ML_FILE, "rows": len(ml_df), "cols": len(ml_df.columns)},
    )
    return ml_df


if __name__ == "__main__":
    df = build_gold_ml_dataset()
    print(f"\n[OK] ML dataset: {len(df)} rows x {len(df.columns)} columns")
    print("\nColumns:")
    for col in df.columns:
        print(f"  {col}")
    print(f"\nSample (Bitcoin):")
    btc = df[df["symbol"] == "bitcoin"]
    if not btc.empty:
        sample_cols = [
            "timestamp", "close", "returns", "rsi",
            "news_count", "sentiment_score", "sent_ma3", "sent_trend",
        ]
        sample_cols = [c for c in sample_cols if c in btc.columns]
        print(btc[sample_cols].tail(5).to_string(index=False))
