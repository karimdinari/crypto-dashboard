from pathlib import Path
import pandas as pd

from app.config.logging_config import get_logger
from app.etl.schema_gold import (
    GOLD_MARKET_FEATURES_COLUMNS,
    GOLD_CORRELATION_COLUMNS,
)
from app.features.market_features import build_market_features
from app.features.correlation import build_correlation_matrix

logger = get_logger(__name__)

SILVER_MARKET_PATH = "lakehouse/silver/market_data/data.parquet"

GOLD_MARKET_DIR = "lakehouse/gold/market_features"
GOLD_MARKET_FILE = "lakehouse/gold/market_features/data.parquet"

GOLD_CORR_DIR = "lakehouse/gold/correlation_matrix"
GOLD_CORR_FILE = "lakehouse/gold/correlation_matrix/data.parquet"


def build_gold_market():
    logger.info("Reading Silver market dataset")

    silver_df = pd.read_parquet(SILVER_MARKET_PATH)

    logger.info("Building market features")
    features_df = build_market_features(silver_df)

    features_df["timestamp"] = pd.to_datetime(
        features_df["timestamp"],
        errors="coerce",
        utc=True,
    )

    features_df = features_df.dropna(subset=["symbol", "timestamp", "close"])
    features_df = features_df.sort_values("timestamp").reset_index(drop=True)

    features_df = features_df[GOLD_MARKET_FEATURES_COLUMNS]

    market_output_dir = Path(GOLD_MARKET_DIR)
    market_output_dir.mkdir(parents=True, exist_ok=True)
    features_df.to_parquet(GOLD_MARKET_FILE, index=False)

    logger.info(f"Gold market features written to {GOLD_MARKET_FILE}")

    logger.info("Building correlation matrix")
    corr_df = build_correlation_matrix(features_df)
    corr_df = corr_df[GOLD_CORRELATION_COLUMNS]

    corr_output_dir = Path(GOLD_CORR_DIR)
    corr_output_dir.mkdir(parents=True, exist_ok=True)
    corr_df.to_parquet(GOLD_CORR_FILE, index=False)

    logger.info(f"Gold correlation matrix written to {GOLD_CORR_FILE}")

    return features_df, corr_df


if __name__ == "__main__":
    build_gold_market()