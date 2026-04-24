"""
Gold Sentiment Aggregates
==========================
Reads Silver news_sentiment/data.parquet and produces two Gold tables:

1. ``gold/sentiment_daily/data.parquet``
   One row per (symbol, date) with aggregated sentiment metrics.
   Used by the dashboard and ML feature store.

2. ``gold/sentiment_signals/data.parquet``
   Simplified signal table (one row per symbol) with the rolling
   sentiment trend for the last 7 days.
   Used by the inference layer / API.

Run from backend/:
    python -m app.etl.gold.build_gold_sentiment

Or import:
    from app.etl.gold.build_gold_sentiment import build_gold_sentiment
    daily_df, signal_df = build_gold_sentiment()
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.config.logging_config import get_logger
from app.config.settings import SILVER_PATH, GOLD_PATH

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SILVER_SENTIMENT_FILE = Path(SILVER_PATH) / "news_sentiment" / "data.parquet"

GOLD_SENTIMENT_DAILY_DIR  = Path(GOLD_PATH) / "sentiment_daily"
GOLD_SENTIMENT_DAILY_FILE = GOLD_SENTIMENT_DAILY_DIR / "data.parquet"

GOLD_SENTIMENT_SIGNAL_DIR  = Path(GOLD_PATH) / "sentiment_signals"
GOLD_SENTIMENT_SIGNAL_FILE = GOLD_SENTIMENT_SIGNAL_DIR / "data.parquet"

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

GOLD_SENTIMENT_DAILY_COLUMNS = [
    "symbol",
    "display_symbol",
    "market_type",
    "date",
    # ── Volume ─────────────────────────────────────────────────────────────
    "news_count",            # total articles scored that day
    "positive_count",        # articles labelled positive
    "neutral_count",
    "negative_count",
    # ── Ratios ─────────────────────────────────────────────────────────────
    "positive_ratio",        # positive_count / news_count
    "negative_ratio",
    # ── Compound metrics ───────────────────────────────────────────────────
    "avg_compound",          # mean compound score  (-1 to +1)
    "min_compound",
    "max_compound",
    "std_compound",          # volatility of sentiment
    # ── Momentum (rolling) ─────────────────────────────────────────────────
    "compound_ma3",          # 3-day moving average of avg_compound
    "compound_ma7",          # 7-day moving average of avg_compound
    # ── Signal ─────────────────────────────────────────────────────────────
    "sentiment_signal",      # "bullish" | "bearish" | "neutral"
]

GOLD_SENTIMENT_SIGNAL_COLUMNS = [
    "symbol",
    "display_symbol",
    "market_type",
    "last_date",             # most recent date with news
    "news_7d",               # article count in last 7 days
    "avg_compound_7d",       # mean compound over last 7 days
    "compound_ma7",          # 7-day MA compound (latest value)
    "positive_ratio_7d",
    "negative_ratio_7d",
    "sentiment_signal",      # "bullish" | "bearish" | "neutral"
    "signal_strength",       # abs(avg_compound_7d)  — 0 to 1
]


# ---------------------------------------------------------------------------
# Signal mapping
# ---------------------------------------------------------------------------

def _compound_to_signal(compound: float) -> str:
    """Map a compound score to a ternary signal label."""
    if compound >= 0.05:
        return "bullish"
    if compound <= -0.05:
        return "bearish"
    return "neutral"


# ---------------------------------------------------------------------------
# Daily aggregation
# ---------------------------------------------------------------------------

def _build_daily(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate per-article rows into one row per (symbol, date).
    Also adds rolling 3-day and 7-day compound moving averages.
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df["date"] = df["timestamp"].dt.date

    agg = (
        df.groupby(["symbol", "display_symbol", "market_type", "date"])
        .agg(
            news_count        = ("news_id",           "count"),
            positive_count    = ("sentiment_label",   lambda x: (x == "positive").sum()),
            neutral_count     = ("sentiment_label",   lambda x: (x == "neutral").sum()),
            negative_count    = ("sentiment_label",   lambda x: (x == "negative").sum()),
            avg_compound      = ("sentiment_compound", "mean"),
            min_compound      = ("sentiment_compound", "min"),
            max_compound      = ("sentiment_compound", "max"),
            std_compound      = ("sentiment_compound", "std"),
        )
        .reset_index()
    )

    # Ratios
    agg["positive_ratio"] = (agg["positive_count"] / agg["news_count"]).round(4)
    agg["negative_ratio"] = (agg["negative_count"] / agg["news_count"]).round(4)
    agg["avg_compound"]   = agg["avg_compound"].round(4)
    agg["min_compound"]   = agg["min_compound"].round(4)
    agg["max_compound"]   = agg["max_compound"].round(4)
    agg["std_compound"]   = agg["std_compound"].fillna(0.0).round(4)

    # Sort before rolling
    agg = agg.sort_values(["symbol", "date"]).reset_index(drop=True)

    # Rolling MAs per symbol
    agg["compound_ma3"] = (
        agg.groupby("symbol")["avg_compound"]
        .transform(lambda x: x.rolling(3, min_periods=1).mean())
        .round(4)
    )
    agg["compound_ma7"] = (
        agg.groupby("symbol")["avg_compound"]
        .transform(lambda x: x.rolling(7, min_periods=1).mean())
        .round(4)
    )

    # Signal from 7-day MA (smoother signal, less noise)
    agg["sentiment_signal"] = agg["compound_ma7"].apply(_compound_to_signal)

    # Enforce column order
    for col in GOLD_SENTIMENT_DAILY_COLUMNS:
        if col not in agg.columns:
            agg[col] = None
    agg = agg[GOLD_SENTIMENT_DAILY_COLUMNS]

    logger.info(
        "Daily sentiment aggregated",
        extra={
            "rows": len(agg),
            "symbols": agg["symbol"].nunique(),
            "date_range": f"{agg['date'].min()} → {agg['date'].max()}",
        },
    )
    return agg


# ---------------------------------------------------------------------------
# Per-symbol signal (7-day rolling)
# ---------------------------------------------------------------------------

def _build_signals(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Produce the latest rolling 7-day sentiment signal per symbol.
    Takes the last 7 rows per symbol from the daily table.
    """
    daily_df = daily_df.copy()
    daily_df["date"] = pd.to_datetime(daily_df["date"])
    daily_df = daily_df.sort_values(["symbol", "date"])

    records = []
    for symbol, grp in daily_df.groupby("symbol"):
        last_7 = grp.tail(7)

        avg_compound_7d   = round(last_7["avg_compound"].mean(), 4)
        positive_ratio_7d = round(last_7["positive_count"].sum() / max(last_7["news_count"].sum(), 1), 4)
        negative_ratio_7d = round(last_7["negative_count"].sum() / max(last_7["news_count"].sum(), 1), 4)

        latest = last_7.iloc[-1]

        records.append(
            {
                "symbol":            symbol,
                "display_symbol":    latest["display_symbol"],
                "market_type":       latest["market_type"],
                "last_date":         str(latest["date"].date() if hasattr(latest["date"], "date") else latest["date"]),
                "news_7d":           int(last_7["news_count"].sum()),
                "avg_compound_7d":   avg_compound_7d,
                "compound_ma7":      round(float(latest["compound_ma7"]), 4),
                "positive_ratio_7d": positive_ratio_7d,
                "negative_ratio_7d": negative_ratio_7d,
                "sentiment_signal":  _compound_to_signal(avg_compound_7d),
                "signal_strength":   round(abs(avg_compound_7d), 4),
            }
        )

    signals_df = pd.DataFrame(records)

    # Enforce column order
    for col in GOLD_SENTIMENT_SIGNAL_COLUMNS:
        if col not in signals_df.columns:
            signals_df[col] = None
    signals_df = signals_df[GOLD_SENTIMENT_SIGNAL_COLUMNS]

    logger.info(
        "Sentiment signals built",
        extra={
            "symbols": len(signals_df),
            "bullish": (signals_df["sentiment_signal"] == "bullish").sum(),
            "neutral": (signals_df["sentiment_signal"] == "neutral").sum(),
            "bearish": (signals_df["sentiment_signal"] == "bearish").sum(),
        },
    )
    return signals_df


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def build_gold_sentiment(
    *,
    write_gold: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Read Silver sentiment → build Gold daily aggregates + signal table.

    Args:
        write_gold: If False, return DataFrames without writing to disk.

    Returns:
        Tuple of (daily_df, signals_df).
    """
    logger.info("Starting Gold sentiment build")

    if not SILVER_SENTIMENT_FILE.exists():
        raise FileNotFoundError(
            f"Silver sentiment file not found: {SILVER_SENTIMENT_FILE}\n"
            "Run first: python -m app.etl.silver.news_sentiment_silver"
        )

    df = pd.read_parquet(SILVER_SENTIMENT_FILE)
    logger.info("Silver sentiment loaded", extra={"rows": len(df)})

    if df.empty:
        logger.warning("Silver sentiment DataFrame is empty — nothing to aggregate.")
        empty_daily   = pd.DataFrame(columns=GOLD_SENTIMENT_DAILY_COLUMNS)
        empty_signals = pd.DataFrame(columns=GOLD_SENTIMENT_SIGNAL_COLUMNS)
        return empty_daily, empty_signals

    daily_df   = _build_daily(df)
    signals_df = _build_signals(daily_df)

    if write_gold:
        GOLD_SENTIMENT_DAILY_DIR.mkdir(parents=True, exist_ok=True)
        daily_df.to_parquet(GOLD_SENTIMENT_DAILY_FILE, index=False)
        logger.info(
            "Gold sentiment_daily written",
            extra={"rows": len(daily_df), "path": str(GOLD_SENTIMENT_DAILY_FILE)},
        )

        GOLD_SENTIMENT_SIGNAL_DIR.mkdir(parents=True, exist_ok=True)
        signals_df.to_parquet(GOLD_SENTIMENT_SIGNAL_FILE, index=False)
        logger.info(
            "Gold sentiment_signals written",
            extra={"rows": len(signals_df), "path": str(GOLD_SENTIMENT_SIGNAL_FILE)},
        )

    return daily_df, signals_df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    daily_df, signals_df = build_gold_sentiment()

    print("\n✅ Gold sentiment tables written")
    print(f"\n📅 sentiment_daily — {len(daily_df)} rows")
    print(f"   Path: {GOLD_SENTIMENT_DAILY_FILE}\n")

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)

    print(daily_df[["display_symbol", "date", "news_count", "avg_compound", "sentiment_signal"]].to_string(index=False))

    print(f"\n📡 sentiment_signals — {len(signals_df)} rows")
    print(f"   Path: {GOLD_SENTIMENT_SIGNAL_FILE}\n")
    print(signals_df.to_string(index=False))