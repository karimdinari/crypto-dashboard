"""
Gold Layer Schemas — v3 (Market + News Sentiment + ML Dataset)
"""

# ============================================================
# MARKET FEATURES (Gold)
# ============================================================

GOLD_MARKET_FEATURES_COLUMNS = [
    # --- Identifiers ---
    "symbol",
    "display_symbol",
    "market_type",
    "timestamp",

    # --- Raw OHLCV ---
    "open",
    "high",
    "low",
    "close",
    "volume",

    # --- Core Features (7) ---
    "returns",              # % price change
    "price_diff",           # Absolute price change
    "ma7",                  # 7-day moving average
    "ma30",                 # 30-day moving average
    "volatility",           # Rolling std of returns
    "volume_change",        # Volume difference
    "correlation",          # Correlation with BTC

    # --- Advanced Technical Features (7 cols from 5 indicators) ---
    "rsi",                  # Relative Strength Index (0-100)
    "macd",                 # MACD line
    "macd_signal",          # MACD signal line
    "macd_histogram",       # MACD histogram
    "day_of_week",          # Day of week (0-6)
    "volume_ma7",           # 7-day volume average
    "relative_volume",      # Volume / volume_ma7

    # --- Metadata ---
    "source",
    "ingestion_time",
]


# ============================================================
# CORRELATION MATRIX (Gold)
# ============================================================

GOLD_CORRELATION_COLUMNS = [
    "symbol_1",
    "symbol_2",
    "correlation_value",
]


# ============================================================
# NEWS AGGREGATES (Gold) — v3 with Sentiment
# ============================================================

GOLD_NEWS_AGGREGATES_COLUMNS = [
    # --- Identifiers ---
    "symbol",
    "display_symbol",
    "market_type",
    "date",

    # --- Volume ---
    "news_count",

    # --- Sentiment (VADER compound: -1 to +1) ---
    "sentiment_score",       # Mean compound score
    "sentiment_positive",    # Mean positive ratio
    "sentiment_negative",    # Mean negative ratio
    "sentiment_neutral",     # Mean neutral ratio
    "sentiment_std",         # Spread / disagreement
    "sentiment_max",         # Most bullish article of the day
    "sentiment_min",         # Most bearish article of the day
]


# ============================================================
# ML DATASET (Gold) — joined market + news features
# ============================================================

GOLD_ML_DATASET_COLUMNS = [
    # --- Identifiers ---
    "symbol",
    "display_symbol",
    "market_type",
    "timestamp",
    "date",

    # --- Raw OHLCV (kept for label generation) ---
    "open",
    "high",
    "low",
    "close",
    "volume",

    # --- Market Technical Features ---
    "returns",
    "price_diff",
    "ma7",
    "ma30",
    "volatility",
    "volume_change",
    "correlation",
    "rsi",
    "macd",
    "macd_signal",
    "macd_histogram",
    "day_of_week",
    "volume_ma7",
    "relative_volume",

    # --- News Sentiment Features ---
    "news_count",
    "sentiment_score",
    "sentiment_positive",
    "sentiment_negative",
    "sentiment_neutral",
    "sentiment_std",
    "sentiment_max",
    "sentiment_min",

    # --- Derived News Features ---
    "sent_ma3",
    "sent_ma7",
    "sent_trend",
    "sent_d1",
    "sent_d2",
    "sent_accel",
    "news_vel1",
    "news_ma7",
    "news_burst",
    "sent_regime",
    "sent_overbought",
    "sent_oversold",
    "sent_lag1",
    "sent_lag2",
    "sent_lag3",
    "sent_lag1_diff",
    "bull_bear_ratio",
    "news_price_divergence",

    # --- Metadata ---
    "source",
    "ingestion_time",
]