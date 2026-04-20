"""
News Stream Kafka Consumer
===========================
Consumes news events from the ``news_stream`` Kafka topic published by
``finnhub_news_ws_producer.py`` and persists them to hourly Bronze
parquet files — same Option-A strategy used by the market tick consumer.

Layout:
    lakehouse/bronze/stream_news/
        date=YYYY-MM-DD/
            hour=HH.parquet

Run from backend/:
    python -m app.ingestion.streaming.news_kafka_consumer
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
    TOPIC_NEWS_STREAM,
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Tuning
# ---------------------------------------------------------------------------

FLUSH_BATCH_SIZE = 50            # news arrives slower than ticks
FLUSH_INTERVAL_SECONDS = 60      # flush at least every minute

GROUP_NEWS_STREAM = "news-stream-consumer"

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

STREAM_NEWS_DIR = Path(BRONZE_PATH) / "stream_news"

NEWS_TICK_COLUMNS: list[str] = [
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
    "consumed_at",
]

DATETIME_COLUMNS: list[str] = ["timestamp", "ingestion_time", "consumed_at"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_isoformat(ts: Any) -> str:
    t = pd.to_datetime(ts, utc=True, errors="coerce")
    if pd.isna(t):
        t = pd.Timestamp.now(tz="UTC")
    else:
        t = t.tz_convert("UTC")
    s = t.isoformat(timespec="milliseconds")
    return s[:-6] + "Z" if s.endswith("+00:00") else s


def _enforce_schema(df: pd.DataFrame) -> pd.DataFrame:
    for col in NEWS_TICK_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[NEWS_TICK_COLUMNS].copy()
    for col in DATETIME_COLUMNS:
        df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")
    return df


def _df_for_parquet_write(df: pd.DataFrame) -> pd.DataFrame:
    """Store datetime columns as UTC ISO strings so viewers show UTC."""
    out = df.copy()
    for col in DATETIME_COLUMNS:
        out[col] = [
            _utc_isoformat(v) if pd.notna(v) else pd.NA
            for v in out[col]
        ]
    return out


def _normalise_article(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Validate and normalise a raw Kafka news message."""
    symbol = raw.get("symbol")
    news_id = raw.get("news_id")
    title = raw.get("title", "")

    if not symbol:
        logger.warning("Skipping article — missing symbol", extra={"raw": str(raw)[:200]})
        return None

    if not news_id:
        logger.warning("Skipping article — missing news_id", extra={"symbol": symbol})
        return None

    if not title:
        logger.warning("Skipping article — missing title", extra={"symbol": symbol})
        return None

    ts_raw = raw.get("timestamp") or raw.get("ingestion_time")
    try:
        timestamp = _utc_isoformat(pd.to_datetime(ts_raw, utc=True, errors="raise"))
    except Exception:
        timestamp = _utc_isoformat(datetime.now(timezone.utc))

    ing_raw = raw.get("ingestion_time", "")
    ingestion_time = _utc_isoformat(pd.to_datetime(ing_raw, utc=True, errors="coerce")) if ing_raw else ""

    return {
        "symbol": str(symbol).strip(),
        "display_symbol": str(raw.get("display_symbol", symbol)).strip(),
        "market_type": str(raw.get("market_type", "unknown")).strip(),
        "source": str(raw.get("source", "finnhub_ws")).strip(),
        "news_id": str(news_id).strip(),
        "timestamp": timestamp,
        "title": str(title)[:500],
        "summary": str(raw.get("summary", ""))[:1000],
        "url": str(raw.get("url", "")),
        "source_name": str(raw.get("source_name", "")),
        "ingestion_time": ingestion_time,
        "consumed_at": _utc_isoformat(datetime.now(timezone.utc)),
    }


def _hourly_file(now: datetime) -> Path:
    date_dir = STREAM_NEWS_DIR / f"date={now.strftime('%Y-%m-%d')}"
    date_dir.mkdir(parents=True, exist_ok=True)
    return date_dir / f"hour={now.strftime('%H')}.parquet"


def _flush_to_bronze(batch: list[dict[str, Any]]) -> int:
    if not batch:
        return 0

    now = datetime.now(timezone.utc)
    out_file = _hourly_file(now)
    tmp_file = out_file.with_suffix(".tmp.parquet")

    new_df = _enforce_schema(pd.DataFrame(batch))
    new_rows = len(new_df)

    if out_file.exists():
        try:
            existing_df = _enforce_schema(pd.read_parquet(out_file))
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        except Exception as exc:
            logger.error(
                "Failed to read existing news file — overwriting",
                extra={"file": str(out_file), "error": str(exc)},
            )
            combined_df = new_df
    else:
        combined_df = new_df

    before = len(combined_df)
    combined_df = (
        combined_df
        .drop_duplicates(subset=["symbol", "news_id"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    dupes_removed = before - len(combined_df)

    try:
        _df_for_parquet_write(combined_df).to_parquet(tmp_file, index=False)
        tmp_file.replace(out_file)
    except Exception as exc:
        logger.error("Failed to write news file", extra={"file": str(out_file), "error": str(exc)})
        if tmp_file.exists():
            tmp_file.unlink(missing_ok=True)
        return 0

    logger.info(
        "Flushed news articles to hourly Bronze file",
        extra={
            "new_rows": new_rows,
            "total_rows": len(combined_df),
            "dupes_removed": dupes_removed,
            "file": out_file.name,
            "partition": out_file.parent.name,
        },
    )
    return new_rows


# ---------------------------------------------------------------------------
# Public read helpers
# ---------------------------------------------------------------------------

def read_all_news(
    bronze_dir: Path | None = None,
    date: str | None = None,
    symbol: str | None = None,
) -> pd.DataFrame:
    """
    Read all hourly news parquet files into one sorted DataFrame.

    Args:
        bronze_dir: Override root directory.
        date:       Restrict to one day — e.g. "2026-04-17".
        symbol:     Restrict to one symbol — e.g. "BTC/USD".

    Returns:
        DataFrame with NEWS_TICK_COLUMNS sorted by timestamp ascending.
    """
    root = bronze_dir or STREAM_NEWS_DIR
    pattern = f"date={date}/*.parquet" if date else "**/*.parquet"

    files = sorted(
        f for f in root.glob(pattern)
        if not f.name.endswith(".tmp.parquet")
    )

    if not files:
        return pd.DataFrame(columns=NEWS_TICK_COLUMNS)

    frames: list[pd.DataFrame] = []
    for f in files:
        try:
            frames.append(pd.read_parquet(f))
        except Exception as exc:
            logger.warning("Skipping unreadable file", extra={"file": str(f), "error": str(exc)})

    if not frames:
        return pd.DataFrame(columns=NEWS_TICK_COLUMNS)

    df = _enforce_schema(pd.concat(frames, ignore_index=True))
    df = df.sort_values("timestamp").reset_index(drop=True)

    if symbol:
        df = df[df["symbol"] == symbol].reset_index(drop=True)

    logger.info("read_all_news complete", extra={"files_read": len(frames), "total_rows": len(df)})
    return df


# ---------------------------------------------------------------------------
# Consumer
# ---------------------------------------------------------------------------

class NewsStreamConsumer:
    """
    Consumes ``news_stream`` events from Kafka and persists them to
    hourly Bronze parquet files under ``bronze/stream_news/``.
    """

    def __init__(
        self,
        flush_batch_size: int = FLUSH_BATCH_SIZE,
        flush_interval: float = FLUSH_INTERVAL_SECONDS,
    ) -> None:
        self.flush_batch_size = flush_batch_size
        self.flush_interval = flush_interval
        self._running = False
        self._consumer = None

    def _get_consumer(self):
        if self._consumer is None:
            from kafka import KafkaConsumer  # type: ignore[import]
            self._consumer = KafkaConsumer(
                TOPIC_NEWS_STREAM,
                **CONSUMER_CONFIG,
                group_id=GROUP_NEWS_STREAM,
            )
            logger.info(
                "Kafka news consumer connected",
                extra={"topic": TOPIC_NEWS_STREAM, "group_id": GROUP_NEWS_STREAM},
            )
        return self._consumer

    def run(self) -> None:
        self._running = True
        consumer = self._get_consumer()
        batch: list[dict[str, Any]] = []
        last_flush = time.monotonic()
        total_consumed = 0
        total_skipped = 0
        total_written = 0

        logger.info(
            "NewsStreamConsumer started",
            extra={
                "topic": TOPIC_NEWS_STREAM,
                "flush_batch_size": self.flush_batch_size,
                "flush_interval_s": self.flush_interval,
                "bronze_dir": str(STREAM_NEWS_DIR),
            },
        )

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

                article = _normalise_article(raw)
                if article is None:
                    total_skipped += 1
                    continue

                batch.append(article)
                total_consumed += 1

                elapsed = time.monotonic() - last_flush
                if len(batch) >= self.flush_batch_size or elapsed >= self.flush_interval:
                    total_written += _flush_to_bronze(batch)
                    batch.clear()
                    last_flush = time.monotonic()

                    logger.info(
                        "News consumer stats",
                        extra={
                            "total_consumed": total_consumed,
                            "total_written": total_written,
                            "total_skipped": total_skipped,
                        },
                    )

        except Exception as exc:
            logger.error("News consumer loop error", extra={"error": str(exc)})
            raise

        finally:
            if batch:
                logger.info("Flushing remaining news on shutdown", extra={"remaining": len(batch)})
                _flush_to_bronze(batch)
            self._cleanup()

    def stop(self) -> None:
        logger.info("Stopping NewsStreamConsumer")
        self._running = False

    def _cleanup(self) -> None:
        if self._consumer:
            try:
                self._consumer.close()
                logger.info("Kafka news consumer closed cleanly")
            except Exception as exc:
                logger.warning("Error closing consumer", extra={"error": str(exc)})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    consumer = NewsStreamConsumer()

    def _handle_signal(signum, frame):
        logger.info("Shutdown signal received", extra={"signum": signum})
        consumer.stop()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    consumer.run()


if __name__ == "__main__":
    main()