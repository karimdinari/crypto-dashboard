GOLD_MARKET_FEATURES_COLUMNS = [
    # Identifiers
    "symbol",
    "display_symbol",
    "market_type",
    "timestamp",
    
    # Raw OHLCV
    "open",
    "high",
    "low",
    "close",
    "volume",
    
    # Basic features (existing)
    "returns",
    "price_diff",
    "ma7",
    "ma30",
    "volatility",
    
    # 🔥 Advanced Technical Indicators
    "rsi",                    # Relative Strength Index
    "macd",                   # MACD line
    "macd_signal",            # MACD signal line
    "macd_histogram",         # MACD histogram
    "bb_upper",               # Bollinger upper band
    "bb_lower",               # Bollinger lower band
    "bb_middle",              # Bollinger middle band
    "bb_position",            # Position within bands
    "atr",                    # Average True Range
    "roc",                    # Rate of Change
    
    # 🔥 Volume Features
    "volume_change",          # Volume % change
    "volume_ma7",             # Volume moving average
    "relative_volume",        # Volume vs average
    "vwap",                   # Volume-weighted avg price
    
    # 🔥 Time Features
    "day_of_week",            # 0-6 (Mon-Sun)
    "day_of_month",           # 1-31
    "month",                  # 1-12
    "quarter",                # 1-4
    "is_month_start",         # Binary
    "is_month_end",           # Binary
    
    # 🔥 Cross-Asset Features
    "btc_dominance",          # BTC market cap %
    "btc_correlation",        # Correlation with BTC
    
    # 🔥 Lag Features
    "close_lag_1",
    "close_lag_2",
    "close_lag_3",
    "close_lag_7",
    "returns_lag_1",
    "returns_lag_2",
    "volume_lag_1",
    
    # Metadata
    "source",
    "ingestion_time",
]