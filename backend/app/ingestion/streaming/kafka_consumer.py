"""
Market Stream Kafka Consumer
=============================
Consumes tick events from the ``market_stream`` Kafka topic published by:
    - binance_ws_producer.py      (crypto  — source: "binance_ws")
    - yfinance_metals_producer.py (metals  — source: "yfinance_stream")
    - finnhub_ws_producer.py      (news/fx — source: "finnhub_ws")  ← friend adds this

FIX: instead of reading + rewriting one giant parquet file on every flush,
each flush writes a small partition file:
    lakehouse/bronze/stream_ticks/
        date=2026-04-14/
            hour=00/
                ticks_<timestamp>.parquet
            hour=01/
                ticks_<timestamp>.parquet
        date=2026-04-15/
            ...

This means every flush is a pure write — no read, no concat, no growing bottleneck.
To query all ticks at once use read_all_ticks() or pandas read_parquet on the root dir.

"""

from __future__ import annotations

import json
import signal
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from app.config.logging_config import get_logger
from app.config.settings import BRONZE_PATH
from app.ingestion.streaming.kafka_config import (
    CONSUMER_CONFIG,
    GROUP_MARKET_STREAM,
    TOPIC_MARKET_STREAM,
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Tuning constants
# ---------------------------------------------------------------------------

FLUSH_BATCH_SIZE       = 100   # flush after this many ticks
FLUSH_INTERVAL_SECONDS = 30    # or after this many seconds, whichever first

# ---------------------------------------------------------------------------
# Bronze output root
# ---------------------------------------------------------------------------

STREAM_BRONZE_DIR = Path(BRONZE_PATH) / "stream_ticks"

# ---------------------------------------------------------------------------
# Canonical schema
# ---------------------------------------------------------------------------

STREAM_TICK_COLUMNS = [
    "symbol",
    "market_type",
    "source",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "timestamp",
    "ingestion_time",
    "consumed_at",
]

KNOWN_SOURCES = {
    "binance_ws",
    "yfinance_stream",
    "finnhub_ws",
}


# ---------------------------------------------------------------------------
# Tick normalisation
# ---------------------------------------------------------------------------

def _normalise_tick(raw: dict[str, Any]) -> dict[str, Any] | None:
    symbol = raw.get("symbol")
    close  = raw.get("close") or raw.get("price")

    if not symbol or close is None:
        logger.warning("Skipping tick — missing symbol or price/close", extra={"raw": str(raw)[:200]})
        return None

    try:
        close = float(close)
    except (TypeError, ValueError):
        logger.warning("Skipping tick — non-numeric close", extra={"close": close})
        return None

    if close <= 0:
        logger.warning("Skipping tick — non-positive close", extra={"close": close})
        return None

    source = str(raw.get("source", "unknown"))
    if source not in KNOWN_SOURCES:
        logger.warning("Tick from unknown source — accepting but flagging", extra={"source": source})

    ts_raw = raw.get("timestamp") or raw.get("ingestion_time")
    try:
        timestamp = pd.to_datetime(ts_raw, utc=True, errors="raise")
    except Exception:
        timestamp = pd.Timestamp.now(tz="UTC")

    open_  = float(raw.get("open",  close) or close)
    high   = float(raw.get("high",  close) or close)
    low    = float(raw.get("low",   close) or close)
    volume = raw.get("volume") or raw.get("quantity")
    try:
        volume = float(volume) if volume is not None else None
    except (TypeError, ValueError):
        volume = None

    return {
        "symbol":         str(symbol).strip(),
        "market_type":    str(raw.get("market_type", "unknown")).strip(),
        "source":         source,
        "open":           open_,
        "high":           high,
        "low":            low,
        "close":          close,
        "volume":         volume,
        "timestamp":      timestamp.isoformat(),
        "ingestion_time": str(raw.get("ingestion_time", "")),
        "consumed_at":    datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Partition writer — pure append, never reads existing files
# ---------------------------------------------------------------------------

def _flush_to_bronze(batch: list[dict[str, Any]]) -> int:
    """
    Write batch as a new partition file under:
        stream_ticks/date=YYYY-MM-DD/hour=HH/ticks_<ts>.parquet

    Pure write — never reads existing data. Fast regardless of total row count.
    Returns number of rows written.
    """
    if not batch:
        return 0

    now      = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    hour_str = now.strftime("%H")
    file_ts  = now.strftime("%H%M%S_%f")

    partition_dir = STREAM_BRONZE_DIR / f"date={date_str}" / f"hour={hour_str}"
    partition_dir.mkdir(parents=True, exist_ok=True)

    out_file = partition_dir / f"ticks_{file_ts}.parquet"

    df = pd.DataFrame(batch)

    for col in STREAM_TICK_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df = df[STREAM_TICK_COLUMNS]

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["volume"]         = pd.to_numeric(df["volume"], errors="coerce")
    df["timestamp"]      = pd.to_datetime(df["timestamp"],      utc=True, errors="coerce")
    df["ingestion_time"] = pd.to_datetime(df["ingestion_time"], utc=True, errors="coerce")
    df["consumed_at"]    = pd.to_datetime(df["consumed_at"],    utc=True, errors="coerce")

    df.to_parquet(out_file, index=False)

    logger.info(
        "Flushed ticks to Bronze partition",
        extra={
            "batch_size": len(batch),
            "partition":  f"date={date_str}/hour={hour_str}",
            "file":       out_file.name,
        },
    )
    return len(batch)


# ---------------------------------------------------------------------------
# Helper: read ALL partitions into one DataFrame (for inspection / Silver)
# ---------------------------------------------------------------------------

def read_all_ticks(
    bronze_dir: Path | None = None,
    date: str | None = None,
) -> pd.DataFrame:
    """
    Read all partition files back into a single DataFrame.

    Args:
        bronze_dir: root stream_ticks dir (defaults to STREAM_BRONZE_DIR)
        date: optional filter e.g. "2026-04-14" to read only one day

    Usage:
        from app.ingestion.streaming.kafka_consumer import read_all_ticks
        df = read_all_ticks()
        df = read_all_ticks(date="2026-04-14")
    """
    root = bronze_dir or STREAM_BRONZE_DIR

    pattern = f"date={date}/**/*.parquet" if date else "**/*.parquet"
    files   = sorted(root.glob(pattern))

    if not files:
        return pd.DataFrame(columns=STREAM_TICK_COLUMNS)

    frames = [pd.read_parquet(f) for f in files]
    df = pd.concat(frames, ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.sort_values("timestamp").reset_index(drop=True)

    return df


# ---------------------------------------------------------------------------
# Consumer
# ---------------------------------------------------------------------------

class MarketStreamConsumer:
    """
    Consumes market_stream ticks from Kafka and writes partitioned Bronze files.
    Each flush is a pure write — no read bottleneck as data grows.
    """

    def __init__(
        self,
        flush_batch_size: int   = FLUSH_BATCH_SIZE,
        flush_interval:   float = FLUSH_INTERVAL_SECONDS,
    ) -> None:
        self.flush_batch_size = flush_batch_size
        self.flush_interval   = flush_interval
        self._running         = False
        self._consumer        = None

    def _get_consumer(self):
        if self._consumer is None:
            try:
                from kafka import KafkaConsumer  # type: ignore[import]
                self._consumer = KafkaConsumer(
                    TOPIC_MARKET_STREAM,
                    **CONSUMER_CONFIG,
                    group_id=GROUP_MARKET_STREAM,
                )
                logger.info(
                    "Kafka consumer connected",
                    extra={"topic": TOPIC_MARKET_STREAM, "group_id": GROUP_MARKET_STREAM},
                )
            except Exception as exc:
                logger.error("Failed to create Kafka consumer", extra={"error": str(exc)})
                raise
        return self._consumer

    def run(self) -> None:
        self._running = True

        logger.info(
            "Starting MarketStreamConsumer",
            extra={
                "topic":            TOPIC_MARKET_STREAM,
                "flush_batch_size": self.flush_batch_size,
                "flush_interval_s": self.flush_interval,
                "storage":          "partitioned (date/hour)",
            },
        )

        consumer       = self._get_consumer()
        batch:          list[dict[str, Any]] = []
        last_flush      = time.monotonic()
        total_consumed  = 0
        total_skipped   = 0
        total_written   = 0

        try:
            for message in consumer:
                if not self._running:
                    break

                try:
                    raw: dict[str, Any] = json.loads(message.value)
                except (json.JSONDecodeError, TypeError) as exc:
                    logger.warning("Failed to deserialise message", extra={"error": str(exc)})
                    total_skipped += 1
                    continue

                tick = _normalise_tick(raw)
                if tick is None:
                    total_skipped += 1
                    continue

                batch.append(tick)
                total_consumed += 1

                elapsed      = time.monotonic() - last_flush
                should_flush = (
                    len(batch) >= self.flush_batch_size
                    or elapsed  >= self.flush_interval
                )

                if should_flush:
                    total_written += _flush_to_bronze(batch)
                    batch.clear()
                    last_flush = time.monotonic()

                    logger.info(
                        "Consumer stats",
                        extra={
                            "total_consumed": total_consumed,
                            "total_written":  total_written,
                            "total_skipped":  total_skipped,
                        },
                    )

        except Exception as exc:
            logger.error("Consumer loop error", extra={"error": str(exc)})
            raise

        finally:
            if batch:
                logger.info("Flushing remaining ticks on shutdown", extra={"remaining": len(batch)})
                _flush_to_bronze(batch)
            self._cleanup()

    def stop(self) -> None:
        logger.info("Stopping MarketStreamConsumer")
        self._running = False

    def _cleanup(self) -> None:
        if self._consumer:
            try:
                self._consumer.close()
                logger.info("Kafka consumer closed cleanly")
            except Exception as exc:
                logger.warning("Error closing Kafka consumer", extra={"error": str(exc)})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    consumer = MarketStreamConsumer()

    def _handle_signal(signum, frame):
        logger.info("Shutdown signal received")
        consumer.stop()

    signal.signal(signal.SIGINT,  _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    consumer.run()


if __name__ == "__main__":
    main()