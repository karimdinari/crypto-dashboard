"""
Kafka configuration for the market streaming pipeline.

Centralizes all Kafka settings pulled from app.config.settings,
and provides producer / consumer config dicts ready to pass to
kafka-python's KafkaProducer and KafkaConsumer.

Usage:
    from app.ingestion.streaming.kafka_config import (
        PRODUCER_CONFIG,
        CONSUMER_CONFIG,
        TOPIC_MARKET_STREAM,
        TOPIC_NEWS_STREAM,
    )
"""

from __future__ import annotations

from app.config.settings import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC_MARKET_STREAM,
    KAFKA_TOPIC_NEWS_STREAM,
)

# ---------------------------------------------------------------------------
# Topic names
# ---------------------------------------------------------------------------

TOPIC_MARKET_STREAM: str = KAFKA_TOPIC_MARKET_STREAM
TOPIC_NEWS_STREAM: str = KAFKA_TOPIC_NEWS_STREAM

# ---------------------------------------------------------------------------
# All known topics (useful for topic-creation scripts / health checks)
# ---------------------------------------------------------------------------

ALL_TOPICS: list[str] = [
    TOPIC_MARKET_STREAM,
    TOPIC_NEWS_STREAM,
]

# ---------------------------------------------------------------------------
# Producer config
# Passed directly to KafkaProducer(**PRODUCER_CONFIG)
# ---------------------------------------------------------------------------

PRODUCER_CONFIG: dict = {
    "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
    # Serialize values to UTF-8 JSON strings (callers encode to bytes)
    "value_serializer": lambda v: v if isinstance(v, bytes) else v.encode("utf-8"),
    "key_serializer": lambda k: k.encode("utf-8") if k else None,
    # Reliability settings
    "acks": "all",           # wait for full ISR acknowledgement
    "retries": 3,
    "retry_backoff_ms": 500,
    # Performance
    "linger_ms": 10,         # small batching window
    "batch_size": 16_384,    # 16 KB
    "compression_type": "gzip",
    "request_timeout_ms": 30_000,
}

# ---------------------------------------------------------------------------
# Consumer config (base — callers add group_id and topic list)
# Passed directly to KafkaConsumer(**CONSUMER_CONFIG, group_id=..., ...)
# ---------------------------------------------------------------------------

CONSUMER_CONFIG: dict = {
    "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
    "value_deserializer": lambda v: v.decode("utf-8"),
    "key_deserializer": lambda k: k.decode("utf-8") if k else None,
    # Start from the beginning when no committed offset exists
    "auto_offset_reset": "earliest",
    "enable_auto_commit": True,
    "auto_commit_interval_ms": 5_000,
    "session_timeout_ms": 30_000,
    "request_timeout_ms": 40_000,
    "max_poll_records": 500,
}

# ---------------------------------------------------------------------------
# Consumer group IDs
# ---------------------------------------------------------------------------

GROUP_MARKET_STREAM: str = "market-stream-consumer"
GROUP_NEWS_STREAM: str = "news-stream-consumer"

# ---------------------------------------------------------------------------
# Topic-level defaults used by admin / topic-creation helpers
# ---------------------------------------------------------------------------

TOPIC_DEFAULTS: dict[str, dict] = {
    TOPIC_MARKET_STREAM: {
        "num_partitions": 3,
        "replication_factor": 1,
        "config": {
            "retention.ms": str(7 * 24 * 60 * 60 * 1_000),   # 7 days
            "cleanup.policy": "delete",
        },
    },
    TOPIC_NEWS_STREAM: {
        "num_partitions": 1,
        "replication_factor": 1,
        "config": {
            "retention.ms": str(3 * 24 * 60 * 60 * 1_000),   # 3 days
            "cleanup.policy": "delete",
        },
    },
}