"""
Bronze schema definitions.

Bronze keeps data close to raw source format, but we still define
minimum required columns for consistency and validation.
"""

BRONZE_CRYPTO_COLUMNS = [
    "symbol",
    "display_symbol",
    "market_type",
    "source",
    "price",
    "market_cap",
    "total_volume",
    "ingestion_time",
    
]

BRONZE_FOREX_COLUMNS = [
    "symbol",
    "display_symbol",
    "market_type",
    "source",
    "base_currency",
    "quote_currency",
    "exchange_rate",
    "ingestion_time",
]

BRONZE_METALS_COLUMNS = [
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
]

BRONZE_NEWS_COLUMNS = [
    "symbol",
    "display_symbol",
    "market_type",
    "source",
    "news_id",
    "timestamp",
    "title",
    "summary",
    "url",
    "source_name",
    "ingestion_time",
]