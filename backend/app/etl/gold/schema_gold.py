"""
Gold layer schemas - 12 Features Version.
"""

GOLD_MARKET_FEATURES_COLUMNS = [
    # ============================================================
    # IDENTIFIERS
    # ============================================================
    "symbol",
    "display_symbol",
    "market_type",
    "timestamp",
    
    # ============================================================
    # RAW OHLCV
    # ============================================================
    "open",
    "high",
    "low",
    "close",
    "volume",
    
    # ============================================================
    # CORE FEATURES (7)
    # ============================================================
    "returns",              # % price change
    "price_diff",           # Absolute price change
    "ma7",                  # 7-day moving average
    "ma30",                 # 30-day moving average
    "volatility",           # Rolling standard deviation
    "volume_change",        # Volume difference
    "correlation",          # Correlation with BTC
    
    # ============================================================
    # ADVANCED FEATURES (5 = 7 columns with MACD components)
    # ============================================================
    "rsi",                  # Relative Strength Index (0-100)
    "macd",                 # MACD line
    "macd_signal",          # MACD signal line
    "macd_histogram",       # MACD histogram
    "day_of_week",          # Day of week (0-6)
    "volume_ma7",           # 7-day volume average
    "relative_volume",      # Volume / volume_ma7
    
    # ============================================================
    # METADATA
    # ============================================================
    "source",
    "ingestion_time",
]
GOLD_CORRELATION_COLUMNS = [
    "symbol_1",
    "symbol_2",
    "correlation_value",
]
GOLD_NEWS_AGGREGATES_COLUMNS = [
    "symbol",
    "display_symbol",
    "market_type",
    "date",
    "news_count",
]

# Total: 25 columns (11 original + 14 features)