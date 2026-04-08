from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from app.config.logging_config import get_logger
from app.config.settings import BRONZE_PATH
from app.utils.validators import validate_required_columns

logger = get_logger(__name__)


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
    path.mkdir(parents=True, exist_ok=True)


def write_bronze_table(
    df: pd.DataFrame,
    dataset_name: str,
    mode: Literal["overwrite", "append"] = "overwrite",
) -> Path:
    if dataset_name not in DATASET_SCHEMA_MAP:
        raise ValueError(f"Unsupported Bronze dataset: {dataset_name}")

    expected_columns = DATASET_SCHEMA_MAP[dataset_name]
    validate_required_columns(df, expected_columns)

    dataset_dir = Path(BRONZE_PATH) / dataset_name
    _ensure_directory(dataset_dir)

    output_file = dataset_dir / "data.parquet"

    if mode == "append" and output_file.exists():
        existing_df = pd.read_parquet(output_file)
        df = pd.concat([existing_df, df], ignore_index=True)

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