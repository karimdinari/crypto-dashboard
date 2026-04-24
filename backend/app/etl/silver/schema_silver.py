"""
Silver layer schemas.

Silver = cleaned, standardized, unified datasets.
"""


# ==========================================
# Unified Market Silver Schema
# ==========================================

SILVER_MARKET_COLUMNS = [
    "symbol",
    "display_symbol",
    "market_type",
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "source",
    "ingestion_time",
]


# ==========================================
# News Silver Schema
# ==========================================

SILVER_NEWS_COLUMNS = [
    "news_id",
    "timestamp",
    "symbol",
    "display_symbol",
    "market_type",
    "title",
    "summary",
    "url",
    "source_name",
    "source",
    "sentiment_label",
    "sentiment_score",
    "sentiment_compound",
    "sentiment_model",
    "ingestion_time",
]