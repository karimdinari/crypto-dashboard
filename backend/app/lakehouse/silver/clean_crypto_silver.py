"""
Reads Bronze crypto_prices/data.parquet,
cleans and normalizes it to the unified Silver schema,
writes Silver crypto_data/data.parquet.

Run from backend/:
    python -m app.lakehouse.silver.clean_crypto_silver
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from app.config.logging_config import get_logger
from app.config.settings import BRONZE_PATH, SILVER_PATH

logger = get_logger("clean_crypto_silver")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BRONZE_FILE = Path(BRONZE_PATH) / "crypto_prices" / "data.parquet"
SILVER_DIR  = Path(SILVER_PATH) / "crypto_data"
SILVER_FILE = SILVER_DIR / "data.parquet"

# ---------------------------------------------------------------------------
# Unified Silver schema — same across crypto / forex / metals
# ---------------------------------------------------------------------------

SILVER_COLUMNS = [
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
    "silver_time",
]


# ---------------------------------------------------------------------------
# Normalize Bronze → Silver
# ---------------------------------------------------------------------------

def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Bronze crypto columns:
        symbol, display_symbol, market_type, source,
        price, market_cap, total_volume, ingestion_time

    Silver mapping:
        price        -> close (spot tick so open/high/low = close)
        total_volume -> volume
        ingestion_time -> timestamp  (no historical bars from /simple/price)
    """
    out = pd.DataFrame()

    out["symbol"]         = df["symbol"].astype(str).str.strip()
    out["display_symbol"] = df["display_symbol"].astype(str).str.strip()
    out["market_type"]    = df["market_type"].astype(str).str.strip()
    out["source"]         = df["source"].astype(str).str.strip()

    price        = pd.to_numeric(df["price"], errors="coerce")
    out["close"] = price
    out["open"]  = price
    out["high"]  = price
    out["low"]   = price

    vol_col       = "total_volume" if "total_volume" in df.columns else None
    out["volume"] = pd.to_numeric(df[vol_col], errors="coerce") if vol_col else pd.NA

    out["timestamp"]      = pd.to_datetime(df["ingestion_time"], utc=True, errors="coerce")
    out["ingestion_time"] = pd.to_datetime(df["ingestion_time"], utc=True, errors="coerce")

    return out


# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------

def _clean(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    df = df.dropna(subset=["symbol", "display_symbol", "timestamp", "close"])
    df = df[df["close"] > 0]
    df = df.drop_duplicates()
    df = df.sort_values("timestamp").reset_index(drop=True)

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    logger.info("Crypto clean", extra={"before": before, "after": len(df)})
    return df


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def _write(df: pd.DataFrame) -> None:
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(SILVER_FILE, index=False)
    logger.info("Silver crypto written", extra={"rows": len(df), "path": str(SILVER_FILE)})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_clean_crypto_silver() -> pd.DataFrame:
    logger.info("Starting crypto Silver cleaning")

    if not BRONZE_FILE.exists():
        raise FileNotFoundError(
            f"Bronze crypto file not found: {BRONZE_FILE}\n"
            "Run ingestion first: python -m app.ingestion.batch.run_batch_ingestion"
        )

    raw = pd.read_parquet(BRONZE_FILE)
    logger.info("Bronze crypto read", extra={"rows": len(raw)})

    silver_time = datetime.now(timezone.utc).isoformat()

    df = _normalize(raw)
    df = _clean(df)
    df["silver_time"] = silver_time

    df = df[[c for c in SILVER_COLUMNS if c in df.columns]]

    _write(df)
    return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    df = run_clean_crypto_silver()

    print("\n✅ Silver crypto_data written")
    print(f"   Rows   : {len(df)}")
    print(f"   Path   : {SILVER_FILE}\n")
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 180)
    print(df[["display_symbol", "market_type", "timestamp", "open", "high", "low", "close", "volume"]].head())