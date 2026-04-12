"""
Reads Bronze metals_prices/data.parquet,
cleans and normalizes it to the unified Silver schema,
writes Silver metals_data/data.parquet.

Run from backend/:
    python -m app.etl.silver.clean_metals_silver
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from app.config.logging_config import get_logger
from app.config.settings import BRONZE_PATH, SILVER_PATH

logger = get_logger("clean_metals_silver")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BRONZE_FILE = Path(BRONZE_PATH) / "metals_prices" / "data.parquet"
SILVER_DIR  = Path(SILVER_PATH) / "metals_data"
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
    Bronze metals columns:
        symbol, display_symbol, market_type, source,
        timestamp, open, high, low, close, volume, ingestion_time

    Already OHLCV — just cast types, enforce UTC on timestamp.
    Volume is nullable (metals CSV often lacks it).
    """
    out = pd.DataFrame()

    out["symbol"]         = df["symbol"].astype(str).str.strip()
    out["display_symbol"] = df["display_symbol"].astype(str).str.strip()
    out["market_type"]    = df["market_type"].astype(str).str.strip()
    out["source"]         = df["source"].astype(str).str.strip()

    out["timestamp"]      = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    out["ingestion_time"] = pd.to_datetime(df["ingestion_time"], utc=True, errors="coerce")

    for col in ["open", "high", "low", "close"]:
        out[col] = pd.to_numeric(df[col], errors="coerce")

    out["volume"] = pd.to_numeric(df["volume"], errors="coerce") if "volume" in df.columns else pd.NA

    return out


# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------

def _clean(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    df = df.dropna(subset=["symbol", "display_symbol", "timestamp", "close"])
    df = df[df["close"] > 0]
    df = df.drop_duplicates()
    df = df.sort_values(["display_symbol", "timestamp"]).reset_index(drop=True)

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    logger.info("Metals clean", extra={"before": before, "after": len(df)})
    return df


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def _write(df: pd.DataFrame) -> None:
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(SILVER_FILE, index=False)
    logger.info("Silver metals written", extra={"rows": len(df), "path": str(SILVER_FILE)})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_clean_metals_silver(*, write_silver: bool = True) -> pd.DataFrame:
    logger.info("Starting metals Silver cleaning")

    if not BRONZE_FILE.exists():
        raise FileNotFoundError(
            f"Bronze metals file not found: {BRONZE_FILE}\n"
            "Run ingestion first: python -m app.ingestion.batch.run_batch_ingestion"
        )

    raw = pd.read_parquet(BRONZE_FILE)
    logger.info("Bronze metals read", extra={"rows": len(raw)})

    silver_time = datetime.now(timezone.utc).isoformat()

    df = _normalize(raw)
    df = _clean(df)
    df["silver_time"] = silver_time

    df = df[[c for c in SILVER_COLUMNS if c in df.columns]]

    if write_silver:
        _write(df)
    return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    df = run_clean_metals_silver()

    print("\n✅ Silver metals_data written")
    print(f"   Rows   : {len(df)}")
    print(f"   Path   : {SILVER_FILE}\n")
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 180)
    print(df[["display_symbol", "market_type", "timestamp", "open", "high", "low", "close", "volume"]].head())
    print("\nBy symbol:")
    print(df.groupby("display_symbol").size().to_string())