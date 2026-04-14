"""
Market Stream Kafka Consumer
=============================
Consumes tick events from the ``market_stream`` Kafka topic published by:
    - binance_ws_producer.py      (crypto  — source: "binance_ws")
    - yfinance_metals_producer.py (metals  — source: "yfinance_stream")
    - finnhub_ws_producer.py      (forex   — source: "finnhub_ws")

Storage strategy — Option A: One parquet file per hour per day
--------------------------------------------------------------
Every flush reads the current hour file (if it exists), appends the
new batch, deduplicates, and rewrites it atomically.

Layout:
    lakehouse/bronze/stream_ticks/
        date=2026-04-14/
            hour=00.parquet    <- all ticks for that hour
            hour=01.parquet
            ...
        date=2026-04-15/
            hour=00.parquet
            ...

File count:
    24 files/day   (vs ~2880 with per-flush strategy)
    168 files/week
    Forever stable — never grows beyond 24 files per active day

Run from backend/:
    python -m app.ingestion.streaming.kafka_consumer
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
# Paths
# ---------------------------------------------------------------------------

STREAM_BRONZE_DIR = Path(BRONZE_PATH) / "stream_ticks"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

STREAM_TICK_COLUMNS: list[str] = [
    "symbol",
    "display_symbol",
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

NUMERIC_COLUMNS: list[str]  = ["open", "high", "low", "close", "volume"]
DATETIME_COLUMNS: list[str] = ["timestamp", "ingestion_time", "consumed_at"]

KNOWN_SOURCES: frozenset[str] = frozenset({
    "binance_ws",
    "yfinance_stream",
    "finnhub_ws",
})


# ---------------------------------------------------------------------------
# Tick normalisation
# Accepts the slightly different field names each producer sends and
# outputs one consistent dict that matches STREAM_TICK_COLUMNS exactly.
# ---------------------------------------------------------------------------

def _safe_float(value: Any, default: float) -> float:
    """Cast value to float, returning default on failure or non-positive."""
    try:
        result = float(value)
        return result if result > 0 else default
    except (TypeError, ValueError):
        return default


def _normalise_tick(raw: dict[str, Any]) -> dict[str, Any] | None:
    """
    Normalise a raw Kafka message dict into a canonical tick row.

    Producer field differences handled here:
        Binance  -> price, timestamp,  quantity
        Finnhub  -> price, event_time, display_symbol
        Metals   -> close, timestamp,  open / high / low present

    Returns None if the tick is invalid and must be skipped.
    """
    # ── required fields ──────────────────────────────────────────────────────
    symbol    = raw.get("symbol")
    close_raw = raw.get("close") or raw.get("price")

    if not symbol:
        logger.warning(
            "Skipping tick — missing symbol",
            extra={"raw": str(raw)[:200]},
        )
        return None

    if close_raw is None:
        logger.warning(
            "Skipping tick — missing close/price",
            extra={"symbol": symbol},
        )
        return None

    try:
        close = float(close_raw)
    except (TypeError, ValueError):
        logger.warning(
            "Skipping tick — non-numeric close",
            extra={"symbol": symbol, "close": close_raw},
        )
        return None

    if close <= 0:
        logger.warning(
            "Skipping tick — non-positive close",
            extra={"symbol": symbol, "close": close},
        )
        return None

    # ── source ───────────────────────────────────────────────────────────────
    source = str(raw.get("source", "unknown"))
    if source not in KNOWN_SOURCES:
        logger.warning(
            "Tick from unknown source — accepting but flagging",
            extra={"source": source, "symbol": symbol},
        )

    # ── timestamp ────────────────────────────────────────────────────────────
    # Binance  -> "timestamp"
    # Finnhub  -> "event_time"
    # fallback -> "ingestion_time" or now
    ts_raw = (
        raw.get("timestamp")
        or raw.get("event_time")
        or raw.get("ingestion_time")
    )
    try:
        timestamp = pd.to_datetime(ts_raw, utc=True, errors="raise")
    except Exception:
        timestamp = pd.Timestamp.now(tz="UTC")

    # ── ohlc ─────────────────────────────────────────────────────────────────
    # Metals sends real open/high/low; Binance/Finnhub only send price.
    # Fill missing values from close so every row has a complete OHLC.
    open_ = _safe_float(raw.get("open"), close)
    high  = _safe_float(raw.get("high"), close)
    low   = _safe_float(raw.get("low"),  close)

    # ── volume ───────────────────────────────────────────────────────────────
    # Binance  -> "quantity"
    # Metals   -> "volume"
    # Finnhub  -> neither (None is acceptable)
    vol_raw = raw.get("volume") or raw.get("quantity")
    try:
        volume: float | None = float(vol_raw) if vol_raw is not None else None
    except (TypeError, ValueError):
        volume = None

    # ── display_symbol ───────────────────────────────────────────────────────
    display_symbol = raw.get("display_symbol") or symbol

    return {
        "symbol":         str(symbol).strip(),
        "display_symbol": str(display_symbol).strip(),
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
# DataFrame helpers
# ---------------------------------------------------------------------------

def _enforce_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Guarantee canonical column order and correct dtypes.
    Called on every batch before writing and on every file read from disk.
    This ensures safe concat even if an older file had different types.
    """
    for col in STREAM_TICK_COLUMNS:
        if col not in df.columns:
            df[col] = None

    df = df[STREAM_TICK_COLUMNS].copy()

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in DATETIME_COLUMNS:
        df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")

    return df


def _build_df(batch: list[dict[str, Any]]) -> pd.DataFrame:
    """Build a typed, schema-enforced DataFrame from a list of tick dicts."""
    return _enforce_schema(pd.DataFrame(batch))


# ---------------------------------------------------------------------------
# Option A — hourly file writer
#
# Strategy:
#   1. Determine the current hour's parquet file path.
#   2. Read it if it already exists.
#   3. Concat existing rows + new batch.
#   4. Deduplicate on (symbol, timestamp) — handles Kafka at-least-once.
#   5. Sort by timestamp.
#   6. Write atomically via a temp file + rename.
#
# Performance:
#   Max file size  ~7 200 rows at 30s / 100-tick flush settings.
#   Read + rewrite of 7 200 rows takes well under 100 ms.
#   File count stays at exactly 24 per active day, forever.
# ---------------------------------------------------------------------------

def _hourly_file(now: datetime) -> Path:
    """
    Return the path for the current hour's parquet file.
    Creates the date directory if needed.

    Pattern:
        stream_ticks/date=YYYY-MM-DD/hour=HH.parquet
    """
    date_dir = STREAM_BRONZE_DIR / f"date={now.strftime('%Y-%m-%d')}"
    date_dir.mkdir(parents=True, exist_ok=True)
    return date_dir / f"hour={now.strftime('%H')}.parquet"


def _flush_to_bronze(batch: list[dict[str, Any]]) -> int:
    """
    Append batch to the current hour's parquet file using Option A strategy.

    Steps:
        1. Build typed DataFrame from batch.
        2. Read existing hourly file if present.
        3. Concat existing + new rows.
        4. Deduplicate on (symbol, timestamp).
        5. Sort by timestamp.
        6. Write atomically: temp file -> rename.

    Returns the number of NEW rows appended.
    Raises nothing — errors are logged and the write is skipped
    so the consumer loop never crashes on a storage failure.
    """
    if not batch:
        return 0

    now      = datetime.now(timezone.utc)
    out_file = _hourly_file(now)
    tmp_file = out_file.with_suffix(".tmp.parquet")

    new_df   = _build_df(batch)
    new_rows = len(new_df)

    # ── merge with existing hour file ─────────────────────────────────────
    if out_file.exists():
        try:
            existing_df = _enforce_schema(pd.read_parquet(out_file))
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        except Exception as exc:
            logger.error(
                "Failed to read existing hourly file — overwriting with new batch",
                extra={
                    "file":  str(out_file),
                    "error": str(exc),
                },
            )
            combined_df = new_df
    else:
        combined_df = new_df

    # ── deduplicate ───────────────────────────────────────────────────────
    before      = len(combined_df)
    combined_df = (
        combined_df
        .drop_duplicates(subset=["symbol", "timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    dupes_removed = before - len(combined_df)

    # ── atomic write ──────────────────────────────────────────────────────
    try:
        combined_df.to_parquet(tmp_file, index=False)
        tmp_file.replace(out_file)          # atomic on same filesystem
    except Exception as exc:
        logger.error(
            "Failed to write hourly file",
            extra={"file": str(out_file), "error": str(exc)},
        )
        if tmp_file.exists():
            tmp_file.unlink(missing_ok=True)
        return 0

    logger.info(
        "Flushed ticks to hourly Bronze file",
        extra={
            "new_rows":       new_rows,
            "total_rows":     len(combined_df),
            "dupes_removed":  dupes_removed,
            "file":           out_file.name,
            "partition":      out_file.parent.name,
        },
    )
    return new_rows


# ---------------------------------------------------------------------------
# Public read helpers
# (used by Silver ETL, inspection scripts, and the future API layer)
# ---------------------------------------------------------------------------

def read_all_ticks(
    bronze_dir:  Path | None = None,
    date:        str  | None = None,
    symbol:      str  | None = None,
    market_type: str  | None = None,
) -> pd.DataFrame:
    """
    Read all hourly parquet files into one sorted DataFrame.

    Args:
        bronze_dir:   override root directory (defaults to STREAM_BRONZE_DIR).
        date:         restrict to one day — e.g. "2026-04-14".
        symbol:       restrict to one symbol — e.g. "BTC/USD".
        market_type:  restrict to one market — e.g. "crypto".

    Returns:
        DataFrame with STREAM_TICK_COLUMNS sorted by timestamp ascending.
        Empty DataFrame (correct columns) when no files are found.

    Examples:
        from app.ingestion.streaming.kafka_consumer import read_all_ticks

        all_ticks    = read_all_ticks()
        today        = read_all_ticks(date="2026-04-14")
        btc          = read_all_ticks(symbol="BTC/USD")
        crypto_today = read_all_ticks(date="2026-04-14", market_type="crypto")
    """
    root    = bronze_dir or STREAM_BRONZE_DIR
    pattern = f"date={date}/*.parquet" if date else "**/*.parquet"

    # Exclude temp files that an in-progress write may have left behind
    files = sorted(
        f for f in root.glob(pattern)
        if not f.suffix == ".tmp.parquet"
        and not f.name.endswith(".tmp.parquet")
    )

    if not files:
        logger.info(
            "read_all_ticks — no files found",
            extra={"root": str(root), "date": date},
        )
        return pd.DataFrame(columns=STREAM_TICK_COLUMNS)

    frames: list[pd.DataFrame] = []
    for f in files:
        try:
            frames.append(pd.read_parquet(f))
        except Exception as exc:
            logger.warning(
                "Skipping unreadable parquet file",
                extra={"file": str(f), "error": str(exc)},
            )

    if not frames:
        return pd.DataFrame(columns=STREAM_TICK_COLUMNS)

    df = _enforce_schema(pd.concat(frames, ignore_index=True))
    df = df.sort_values("timestamp").reset_index(drop=True)

    # ── optional filters ──────────────────────────────────────────────────
    if symbol:
        df = df[df["symbol"] == symbol].reset_index(drop=True)
    if market_type:
        df = df[df["market_type"] == market_type].reset_index(drop=True)

    logger.info(
        "read_all_ticks complete",
        extra={
            "files_read":  len(frames),
            "total_rows":  len(df),
            "filters":     {"date": date, "symbol": symbol, "market_type": market_type},
        },
    )
    return df


def read_latest_per_symbol(bronze_dir: Path | None = None) -> pd.DataFrame:
    """
    Return the single most recent tick for each symbol.

    Useful for:
        - /api/stream/latest endpoint
        - Dashboard current-price display
        - Sanity checks after pipeline runs

    Returns DataFrame with one row per symbol sorted by symbol name.
    """
    df = read_all_ticks(bronze_dir=bronze_dir)

    if df.empty:
        return df

    latest = (
        df.sort_values("timestamp")
          .groupby("symbol", sort=False)
          .last()
          .reset_index()
          .sort_values("symbol")
          .reset_index(drop=True)
    )

    logger.info(
        "read_latest_per_symbol complete",
        extra={"symbols": latest["symbol"].tolist()},
    )
    return latest


# ---------------------------------------------------------------------------
# Consumer
# ---------------------------------------------------------------------------

class MarketStreamConsumer:
    """
    Consumes ``market_stream`` ticks from Kafka and persists them to
    hourly Bronze parquet files (Option A).

    Flush triggers (whichever comes first):
        - Batch reaches ``flush_batch_size`` rows.
        - ``flush_interval`` seconds have elapsed since the last flush.

    Each flush is a read-append-rewrite of the current hour file.
    At default settings the hourly file stays well under 10 000 rows,
    making each flush complete in under 100 ms.
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

    # ------------------------------------------------------------------
    # Kafka consumer (lazy init — connect only when run() is called)
    # ------------------------------------------------------------------

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
                    extra={
                        "topic":    TOPIC_MARKET_STREAM,
                        "group_id": GROUP_MARKET_STREAM,
                    },
                )
            except Exception as exc:
                logger.error(
                    "Failed to create Kafka consumer",
                    extra={"error": str(exc)},
                )
                raise
        return self._consumer

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Start consuming. Blocks until stop() is called or the process
        receives SIGINT / SIGTERM.
        """
        self._running  = True
        consumer       = self._get_consumer()
        batch:           list[dict[str, Any]] = []
        last_flush       = time.monotonic()
        total_consumed   = 0
        total_skipped    = 0
        total_written    = 0

        logger.info(
            "MarketStreamConsumer started",
            extra={
                "topic":            TOPIC_MARKET_STREAM,
                "flush_batch_size": self.flush_batch_size,
                "flush_interval_s": self.flush_interval,
                "storage":          "hourly parquet — Option A",
                "bronze_dir":       str(STREAM_BRONZE_DIR),
            },
        )

        try:
            for message in consumer:
                if not self._running:
                    break

                # ── deserialise ──────────────────────────────────────────
                try:
                    raw: dict[str, Any] = json.loads(message.value)
                except (json.JSONDecodeError, TypeError) as exc:
                    logger.warning(
                        "Failed to deserialise message",
                        extra={"error": str(exc)},
                    )
                    total_skipped += 1
                    continue

                # ── normalise ────────────────────────────────────────────
                tick = _normalise_tick(raw)
                if tick is None:
                    total_skipped += 1
                    continue

                batch.append(tick)
                total_consumed += 1

                # ── flush decision ───────────────────────────────────────
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
            # Always flush whatever is left in the buffer on shutdown
            if batch:
                logger.info(
                    "Flushing remaining ticks on shutdown",
                    extra={"remaining": len(batch)},
                )
                _flush_to_bronze(batch)

            self._cleanup()

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    def stop(self) -> None:
        """Signal the run loop to exit after the current message."""
        logger.info("Stopping MarketStreamConsumer")
        self._running = False

    def _cleanup(self) -> None:
        if self._consumer:
            try:
                self._consumer.close()
                logger.info("Kafka consumer closed cleanly")
            except Exception as exc:
                logger.warning(
                    "Error closing Kafka consumer",
                    extra={"error": str(exc)},
                )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    consumer = MarketStreamConsumer()

    def _handle_signal(signum, frame):
        logger.info("Shutdown signal received", extra={"signum": signum})
        consumer.stop()

    signal.signal(signal.SIGINT,  _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    consumer.run()


if __name__ == "__main__":
    main()