from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from app.config.assets import ALL_MARKET_ASSETS
from app.config.logging_config import get_logger
from app.config.settings import BRONZE_PATH, GOLD_PATH, SILVER_PATH

logger = get_logger(__name__)

GOLD_MARKET_FEATURES = Path(GOLD_PATH) / "market_features" / "data.parquet"
GOLD_CORRELATION = Path(GOLD_PATH) / "correlation_matrix" / "data.parquet"
SILVER_MARKET = Path(SILVER_PATH) / "market_data" / "data.parquet"


def _display_to_name() -> dict[str, str]:
    return {a["display_symbol"]: a["name"] for a in ALL_MARKET_ASSETS}


def _display_to_market() -> dict[str, str]:
    return {a["display_symbol"]: a["market_type"] for a in ALL_MARKET_ASSETS}


def load_gold_market_enriched() -> pd.DataFrame:
    """
    Load Gold market features and add ``ma20`` / ``ma50`` from rolling closes
    (same window semantics as classic TA on the Gold series).
    """
    if not GOLD_MARKET_FEATURES.is_file():
        logger.warning("Gold market features parquet missing", extra={"path": str(GOLD_MARKET_FEATURES)})
        return pd.DataFrame()

    df = pd.read_parquet(GOLD_MARKET_FEATURES)
    if df.empty:
        return df

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["display_symbol", "timestamp", "close"])
    df = df.sort_values(["display_symbol", "timestamp"]).reset_index(drop=True)

    g = df.groupby("display_symbol", sort=False)["close"]
    df["ma20"] = g.transform(lambda s: s.rolling(20, min_periods=1).mean())
    df["ma50"] = g.transform(lambda s: s.rolling(50, min_periods=1).mean())
    return df


def latest_per_display_symbol(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df.sort_values("timestamp").groupby("display_symbol", as_index=False).last()


def format_volume(v: Any) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    if x >= 1e9:
        return f"{x / 1e9:.1f}B"
    if x >= 1e6:
        return f"{x / 1e6:.1f}M"
    if x >= 1e3:
        return f"{x / 1e3:.1f}K"
    if x <= 0:
        return "—"
    return f"{x:.0f}"


def anomalies_for_row(row: pd.Series) -> list[str]:
    out: list[str] = []
    vol = float(row.get("volatility", 0) or 0)
    if vol > 3.5:
        out.append("Elevated volatility regime")
    rsi = float(row.get("rsi", 50) or 50)
    if rsi > 72:
        out.append("RSI stretched (overbought)")
    elif rsi < 28:
        out.append("RSI stretched (oversold)")
    return out
