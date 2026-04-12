"""
Merged market Silver table only (writes ``silver/market_data/data.parquet``).

Does not write per-asset folders (``crypto_data``, ``forex_data``, ``metals_data``).

Run from backend/:
    python -m app.etl.silver.clean_market_silver
"""
import pandas as pd
from pathlib import Path

from app.config.logging_config import get_logger
from app.config.settings import SILVER_PATH
from app.etl.silver.schema_silver import SILVER_MARKET_COLUMNS

from app.etl.silver.clean_crypto_silver import run_clean_crypto_silver
from app.etl.silver.clean_forex_silver import run_clean_forex_silver
from app.etl.silver.clean_metals_silver import run_clean_metals_silver

logger = get_logger(__name__)

SILVER_MARKET_DIR = Path(SILVER_PATH) / "market_data"
SILVER_MARKET_FILE = SILVER_MARKET_DIR / "data.parquet"


def _prepare_for_concat(df: pd.DataFrame) -> pd.DataFrame:
    """Same columns + dtypes before concat (avoids pandas concat FutureWarning)."""
    out = df.loc[:, SILVER_MARKET_COLUMNS].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="coerce")
    out["ingestion_time"] = pd.to_datetime(out["ingestion_time"], utc=True, errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def build_market_silver():
    logger.info("Reading cleaned datasets")

    # Only write silver/market_data — not separate crypto/forex/metals folders
    crypto_df = run_clean_crypto_silver(write_silver=False)
    forex_df = run_clean_forex_silver(write_silver=False)
    metals_df = run_clean_metals_silver(write_silver=False)

    logger.info("Merging datasets")

    market_df = pd.concat(
        [
            _prepare_for_concat(crypto_df),
            _prepare_for_concat(forex_df),
            _prepare_for_concat(metals_df),
        ],
        ignore_index=True,
        sort=False,
    )

    logger.info("Cleaning merged dataset")

    # ensure timestamp
    market_df["timestamp"] = pd.to_datetime(
        market_df["timestamp"],
        errors="coerce",
        utc=True
    )

    # numeric conversions
    for col in ["open", "high", "low", "close", "volume"]:
        if col in market_df.columns:
            market_df[col] = pd.to_numeric(
                market_df[col],
                errors="coerce"
            )

    # drop bad rows
    market_df = market_df.dropna(subset=["symbol", "timestamp", "close"])

    # remove duplicates
    market_df = market_df.drop_duplicates(
        subset=["symbol", "timestamp"]
    )

    # sort
    market_df = market_df.sort_values("timestamp")

    # enforce schema
    market_df = market_df[SILVER_MARKET_COLUMNS]

    # reset index
    market_df = market_df.reset_index(drop=True)

    SILVER_MARKET_DIR.mkdir(parents=True, exist_ok=True)
    market_df.to_parquet(SILVER_MARKET_FILE, index=False)

    logger.info(f"Silver market dataset written to {SILVER_MARKET_FILE}")

    return market_df


if __name__ == "__main__":
    build_market_silver()