"""
Gold layer schemas.
Gold = analytics-ready and ML-ready datasets.
"""

GOLD_MARKET_FEATURES_COLUMNS = [
    "symbol",
    "display_symbol",
    "market_type",
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "returns",
    "price_diff",
    "ma7",
    "ma30",
    "volatility",
    "source",
    "ingestion_time",
]

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