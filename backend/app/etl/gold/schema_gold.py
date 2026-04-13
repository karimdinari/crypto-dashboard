"""
Gold layer schemas.
Gold = analytics-ready and ML-ready datasets.
Updated to match all implemented features.
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
    # PRICE FEATURES
    # ============================================================
    "returns",              # % change
    "price_diff",           # Absolute change
    "ma7",                  # 7-day MA
    "ma14",                 # 14-day MA
    "ma30",                 # 30-day MA
    "ema7",                 # 7-day EMA
    "ema14",                # 14-day EMA
    "volatility",           # Rolling std of returns
    
    # ============================================================
    # TECHNICAL INDICATORS
    # ============================================================
    "rsi",                  # Relative Strength Index
    "macd",                 # MACD line
    "macd_signal",          # MACD signal line
    "macd_histogram",       # MACD histogram
    "bb_upper",             # Bollinger upper band
    "bb_lower",             # Bollinger lower band
    "bb_middle",            # Bollinger middle band
    "bb_position",          # Position within bands (0-1)
    "atr",                  # Average True Range
    "roc",                  # Rate of Change
    "stoch_k",              # Stochastic %K
    "stoch_d",              # Stochastic %D
    
    # ============================================================
    # VOLUME FEATURES
    # ============================================================
    "volume_change",        # Volume % change
    "volume_ma7",           # Volume 7-day MA
    "relative_volume",      # Current / average volume
    "vwap",                 # Volume-weighted average price
    "vpt",                  # Volume Price Trend
    
    # ============================================================
    # TIME FEATURES
    # ============================================================
    "day_of_week",          # 0=Monday, 6=Sunday
    "day_of_month",         # 1-31
    "month",                # 1-12
    "quarter",              # 1-4
    "is_month_start",       # Binary (0 or 1)
    "is_month_end",         # Binary (0 or 1)
    "is_weekend",           # Binary (0 or 1)
    "day_of_week_sin",      # Cyclical encoding (sin)
    "day_of_week_cos",      # Cyclical encoding (cos)
    "month_sin",            # Cyclical encoding (sin)
    "month_cos",            # Cyclical encoding (cos)
    
    # ============================================================
    # CROSS-ASSET FEATURES
    # ============================================================
    "btc_correlation",      # Correlation with Bitcoin
    "btc_dominance",        # BTC market cap %
    "beta",                 # Beta relative to Bitcoin
    
    # ============================================================
    # LAG FEATURES - PRICE
    # ============================================================
    "close_lag_1",          # Price 1 day ago
    "close_lag_2",          # Price 2 days ago
    "close_lag_3",          # Price 3 days ago
    "close_lag_7",          # Price 1 week ago
    "close_lag_14",         # Price 2 weeks ago
    
    # ============================================================
    # LAG FEATURES - RETURNS
    # ============================================================
    "returns_lag_1",        # Returns 1 day ago
    "returns_lag_2",        # Returns 2 days ago
    "returns_lag_3",        # Returns 3 days ago
    "returns_lag_7",        # Returns 1 week ago
    
    # ============================================================
    # LAG FEATURES - VOLUME
    # ============================================================
    "volume_lag_1",         # Volume 1 day ago
    "volume_lag_2",         # Volume 2 days ago
    "volume_lag_3",         # Volume 3 days ago
    
    # ============================================================
    # LAG FEATURES - VOLATILITY
    # ============================================================
    "volatility_lag_1",     # Volatility 1 day ago
    "volatility_lag_2",     # Volatility 2 days ago
    "volatility_lag_3",     # Volatility 3 days ago
    
    # ============================================================
    # METADATA
    # ============================================================
    "source",
    "ingestion_time",
]

# Total columns: 63


GOLD_NEWS_AGGREGATES_COLUMNS = [
    "symbol",
    "display_symbol",
    "market_type",
    "date",
    "news_count",
]

GOLD_CORRELATION_COLUMNS = [
    "symbol_1",
    "symbol_2",
    "correlation_value",
]