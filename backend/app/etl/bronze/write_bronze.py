"""
Bronze layer writer utility.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from app.config.logging_config import get_logger
from app.config.settings import BRONZE_PATH
from app.utils.validation_utils import validate_required_columns


logger = get_logger(__name__)


def _dedupe_after_append(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    """Drop duplicate business keys so daily re-runs do not stack identical rows."""
    if df.empty:
        return df
    if dataset_name == "crypto_prices" and "symbol" in df.columns:
        if "timestamp" not in df.columns:
            return df.drop_duplicates(subset=["symbol", "ingestion_time"], keep="last", ignore_index=True)
        has_ts = df["timestamp"].notna()
        without_ts = df.loc[~has_ts]
        with_ts = df.loc[has_ts].drop_duplicates(
            subset=["symbol", "timestamp"], keep="last", ignore_index=True
        )
        return pd.concat([without_ts, with_ts], ignore_index=True)
    if dataset_name == "forex_rates" and "symbol" in df.columns:
        if "timestamp" not in df.columns:
            return df.drop_duplicates(subset=["symbol", "ingestion_time"], keep="last", ignore_index=True)
        has_ts = df["timestamp"].notna()
        without_ts = df.loc[~has_ts]
        with_ts = df.loc[has_ts].drop_duplicates(
            subset=["symbol", "timestamp"], keep="last", ignore_index=True
        )
        return pd.concat([without_ts, with_ts], ignore_index=True)
    if dataset_name == "metals_prices" and "symbol" in df.columns and "timestamp" in df.columns:
        has_ts = df["timestamp"].notna()
        without_ts = df.loc[~has_ts]
        with_ts = df.loc[has_ts].drop_duplicates(
            subset=["symbol", "timestamp"], keep="last", ignore_index=True
        )
        return pd.concat([without_ts, with_ts], ignore_index=True)
    if dataset_name == "news" and "news_id" in df.columns:
        return df.drop_duplicates(subset=["news_id"], keep="last", ignore_index=True)
    return df


DATASET_SCHEMA_MAP = {
    "crypto_prices": [
        "symbol",
        "display_symbol",
        "market_type",
        "source",
        "price",
        "market_cap",
        "total_volume",
        "ingestion_time",
    ],
    "forex_rates": [
        "symbol",
        "display_symbol",
        "market_type",
        "source",
        "base_currency",
        "quote_currency",
        "exchange_rate",
        "ingestion_time",
    ],
    "metals_prices": [
        "symbol",
        "display_symbol",
        "market_type",
        "source",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "ingestion_time",
    ],
    "news": [
        "symbol",
        "display_symbol",
        "market_type",
        "source",
        "news_id",
        "timestamp",
        "title",
        "summary",
        "url",
        "source_name",
        "ingestion_time",
    ],
}


def _ensure_directory(path: Path) -> None:
    """Create directory if it doesn't exist"""
    path.mkdir(parents=True, exist_ok=True)


def _validate_required_columns(df: pd.DataFrame, expected_columns: list[str]) -> None:
    """
    Validate that DataFrame has all required columns.
    
    Args:
        df: DataFrame to validate
        expected_columns: List of required column names
        
    Raises:
        ValueError: If required columns are missing
    """
    missing = set(expected_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def write_bronze_table(
    df: pd.DataFrame,
    dataset_name: str,
    mode: Literal["overwrite", "append"] = "overwrite",
) -> Path:
    """
    Write DataFrame to Bronze layer.
    
    Args:
        df: DataFrame to write
        dataset_name: Name of the dataset (e.g., 'crypto_prices')
        mode: Write mode - 'overwrite' or 'append'
        
    Returns:
        Path to written file
        
    Raises:
        ValueError: If dataset name is invalid or columns are missing
    """
    if dataset_name not in DATASET_SCHEMA_MAP:
        raise ValueError(f"Unsupported Bronze dataset: {dataset_name}")

    if df is None or df.empty:
        logger.warning(
            "Skipping Bronze write — empty dataframe",
            extra={"dataset_name": dataset_name},
        )
        return Path(BRONZE_PATH) / dataset_name / "data.parquet"

    expected_columns = DATASET_SCHEMA_MAP[dataset_name]
    _validate_required_columns(df, expected_columns)

    # Keep timestamp dtype consistent across append runs (e.g., CSV history + API snapshot).
    if "timestamp" in df.columns:
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")

    dataset_dir = Path(BRONZE_PATH) / dataset_name
    _ensure_directory(dataset_dir)

    output_file = dataset_dir / "data.parquet"

    if mode == "append" and output_file.exists():
        existing_df = pd.read_parquet(output_file)
        if "timestamp" in existing_df.columns:
            existing_df["timestamp"] = pd.to_datetime(
                existing_df["timestamp"], utc=True, errors="coerce"
            )
        df = pd.concat([existing_df, df], ignore_index=True)
        df = _dedupe_after_append(df, dataset_name)

    df.to_parquet(output_file, index=False)

    logger.info(
        "Bronze dataset written",
        extra={
            "dataset_name": dataset_name,
            "rows": len(df),
            "output_path": str(output_file),
            "mode": mode,
        },
    )

    return output_file