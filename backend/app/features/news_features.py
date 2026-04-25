"""
News Sentiment Feature Engineering
====================================
Transforms raw news aggregates (with VADER sentiment) into ML-ready features:

  1. Sentiment momentum  — rolling 3-day & 7-day sentiment averages
  2. Sentiment divergence — news bullish while price falls (contrarian signal)
  3. News velocity        — rate-of-change in article count (attention surge)
  4. Sentiment regime     — overbought/oversold news optimism bucket
  5. Sentiment-volume interaction — high-news + high-volume confirmation
  6. Cross-day lags       — yesterday & 2-days-ago sentiment
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.config.logging_config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_fill(series: pd.Series, fill: float = 0.0) -> pd.Series:
    return series.fillna(fill)


def _to_naive_datetime(series: pd.Series) -> pd.Series:
    """
    Convert a datetime Series to tz-naive datetime64[ns].
    Handles both tz-aware (UTC or other) and already tz-naive inputs.
    """
    s = pd.to_datetime(series, errors="coerce")
    if s.dt.tz is not None:
        s = s.dt.tz_convert(None)   # tz-aware → tz-naive
    return s.dt.normalize()


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_news_features(
    df: pd.DataFrame,
    market_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Compute rolling & derived news sentiment features.

    Args:
        df: Gold news aggregate per (symbol, date) with columns:
                symbol, date, news_count,
                sentiment_score, sentiment_positive,
                sentiment_negative, sentiment_neutral
        market_df: Optional Gold market parquet for divergence signals.
                   Must contain (symbol, timestamp, returns).

    Returns:
        DataFrame with additional news feature columns.
    """
    df = df.copy()
    df["date"] = _to_naive_datetime(df["date"])   # always tz-naive date key
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)

    grp = df.groupby("symbol", group_keys=False)

    # ---- 1. Sentiment momentum -------------------------------------------
    df["sent_ma3"] = grp["sentiment_score"].transform(
        lambda s: s.rolling(3, min_periods=1).mean()
    )
    df["sent_ma7"] = grp["sentiment_score"].transform(
        lambda s: s.rolling(7, min_periods=1).mean()
    )
    df["sent_trend"] = df["sent_ma3"] - df["sent_ma7"]   # short vs long term

    # ---- 2. Sentiment velocity -------------------------------------------
    df["sent_d1"]    = grp["sentiment_score"].transform(lambda s: s.diff(1))
    df["sent_d2"]    = grp["sentiment_score"].transform(lambda s: s.diff(2))
    df["sent_accel"] = df["sent_d1"] - df["sent_d2"]     # acceleration

    # ---- 3. News velocity -----------------------------------------------
    df["news_vel1"] = grp["news_count"].transform(lambda s: s.diff(1))
    df["news_ma7"]  = grp["news_count"].transform(
        lambda s: s.rolling(7, min_periods=1).mean()
    )
    # Relative news burst: today vs 7-day average
    df["news_burst"] = df["news_count"] / (df["news_ma7"] + 1e-9)

    # ---- 4. Sentiment regime (categorical + binary) ----------------------
    # Rolling 30-day quantiles for regime detection
    def _regime(s: pd.Series) -> pd.Series:
        q75 = s.rolling(30, min_periods=5).quantile(0.75)
        q25 = s.rolling(30, min_periods=5).quantile(0.25)
        regime = pd.Series(1, index=s.index)   # neutral
        regime[s > q75] = 2                    # bullish extreme
        regime[s < q25] = 0                    # bearish extreme
        return regime

    df["sent_regime"] = grp["sentiment_score"].transform(_regime)
    df["sent_overbought"] = (df["sent_regime"] == 2).astype(int)
    df["sent_oversold"]   = (df["sent_regime"] == 0).astype(int)

    # ---- 5. Sentiment lags ----------------------------------------------
    for lag in [1, 2, 3]:
        df[f"sent_lag{lag}"] = grp["sentiment_score"].transform(
            lambda s, l=lag: s.shift(l)
        )
    df["sent_lag1_diff"] = df["sentiment_score"] - df["sent_lag1"]

    # ---- 6. Bull/Bear ratio -------------------------------------------
    eps = 1e-9
    df["bull_bear_ratio"] = df["sentiment_positive"] / (
        df["sentiment_negative"] + eps
    )
    df["bull_bear_ratio"] = df["bull_bear_ratio"].clip(0, 10)

    # ---- 7. News-market divergence (requires market_df) -----------------
    if market_df is not None:
        df = _add_divergence(df, market_df)
    else:
        df["news_price_divergence"] = 0.0

    # ---- Fill NaN -------------------------------------------------------
    news_feat_cols = [
        "sent_ma3", "sent_ma7", "sent_trend",
        "sent_d1", "sent_d2", "sent_accel",
        "news_vel1", "news_ma7", "news_burst",
        "sent_regime", "sent_overbought", "sent_oversold",
        "sent_lag1", "sent_lag2", "sent_lag3", "sent_lag1_diff",
        "bull_bear_ratio", "news_price_divergence",
    ]
    for col in news_feat_cols:
        if col in df.columns:
            df[col] = _safe_fill(df[col], 0.0)

    logger.info(
        f"News features built",
        extra={"rows": len(df), "features": len(news_feat_cols)},
    )
    return df


def _add_divergence(news_df: pd.DataFrame, market_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute divergence: sentiment going up while returns going down (or vice versa).
    Positive divergence = news bullish but market bearish (potential reversal signal).
    """
    # Build tz-naive date key from market timestamps
    market_df["date"] = _to_naive_datetime(market_df["timestamp"])  # tz-naive

    # Use last daily close return per symbol per date
    daily_ret = (
        market_df.sort_values(["symbol", "timestamp"])
        .groupby(["symbol", "date"])["returns"]
        .last()
        .reset_index()
        .rename(columns={"returns": "daily_return"})
    )  # daily_ret["date"] is tz-naive

    # Also make news_df date tz-naive before merging
    news_merge = news_df.copy()
    news_merge["date"] = _to_naive_datetime(news_merge["date"])

    merged = news_merge.merge(daily_ret, on=["symbol", "date"], how="left")

    # Divergence: sentiment direction vs price direction
    # +1 = both agree, -1 = diverge, 0 = neutral
    sent_sign  = np.sign(merged["sentiment_score"].fillna(0))
    price_sign = np.sign(merged["daily_return"].fillna(0))
    merged["news_price_divergence"] = (sent_sign - price_sign) / 2.0  # range [-1, 1]

    news_df["news_price_divergence"] = merged["news_price_divergence"].values
    return news_df


# ---------------------------------------------------------------------------
# Column list (for schema)
# ---------------------------------------------------------------------------

NEWS_FEATURE_COLUMNS = [
    "sent_ma3", "sent_ma7", "sent_trend",
    "sent_d1", "sent_d2", "sent_accel",
    "news_vel1", "news_ma7", "news_burst",
    "sent_regime", "sent_overbought", "sent_oversold",
    "sent_lag1", "sent_lag2", "sent_lag3", "sent_lag1_diff",
    "bull_bear_ratio", "news_price_divergence",
]
