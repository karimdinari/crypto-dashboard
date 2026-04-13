"""
yFinance Metals Streaming Producer
====================================
Polls Yahoo Finance for live metals prices (XAU/USD, XAG/USD) at a
configurable interval and publishes tick events to the Kafka topic
``market_stream``.

yFinance does not provide a true WebSocket — this producer simulates
streaming by polling the ``fast_info`` endpoint (~1-minute delayed).

No API key required.


"""

from __future__ import annotations

import json
import signal
import time
from datetime import datetime, timezone
from typing import Any

from app.config.logging_config import get_logger
from app.config.settings import (
    STREAM_RECONNECT_DELAY_SECONDS,
    STREAM_POLL_INTERVAL_SECONDS,
)
from app.config.assets import METALS_ASSETS
from app.ingestion.streaming.kafka_config import (
    PRODUCER_CONFIG,
    TOPIC_MARKET_STREAM,
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Symbol mapping: our display_symbol → yFinance ticker
# ---------------------------------------------------------------------------

SYMBOL_TO_YF: dict[str, str] = {
    "XAU/USD": "GC=F",   # Gold futures
    "XAG/USD": "SI=F",   # Silver futures
}

# Default poll interval (seconds) — override via STREAM_POLL_INTERVAL_SECONDS
DEFAULT_POLL_INTERVAL = max(STREAM_POLL_INTERVAL_SECONDS, 15)  # yFinance rate-limit safety

# ---------------------------------------------------------------------------
# Tick builder
# ---------------------------------------------------------------------------

def _fetch_tick(display_symbol: str, yf_ticker: str, asset: dict) -> dict[str, Any] | None:
    """
    Fetch the latest price for one metals symbol from yFinance.
    Returns a standardised tick dict or None on failure.
    """
    try:
        import yfinance as yf  # lazy import — only required at runtime
    except ImportError as exc:
        raise ImportError(
            "yfinance is not installed. Add it to requirements.txt:\n"
            "    yfinance>=0.2.40,<1"
        ) from exc

    try:
        ticker = yf.Ticker(yf_ticker)
        info = ticker.fast_info

        price = getattr(info, "last_price", None)
        if price is None:
            # Fallback: pull 1-day history and take last close
            hist = ticker.history(period="1d", interval="1m")
            if hist.empty:
                logger.warning(
                    "No price data returned from yFinance",
                    extra={"symbol": display_symbol, "yf_ticker": yf_ticker},
                )
                return None
            price = float(hist["Close"].iloc[-1])

        return {
            "symbol":         asset["display_symbol"],
            "market_type":    "metals",
            "source":         "yfinance_stream",
            "open":           float(getattr(info, "open", price) or price),
            "high":           float(getattr(info, "day_high", price) or price),
            "low":            float(getattr(info, "day_low",  price) or price),
            "close":          float(price),
            "volume":         float(getattr(info, "shares", None) or 0) or None,
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "ingestion_time": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        logger.error(
            "yFinance fetch failed",
            extra={"symbol": display_symbol, "yf_ticker": yf_ticker, "error": str(exc)},
        )
        return None


# ---------------------------------------------------------------------------
# Producer
# ---------------------------------------------------------------------------

class YFinanceMetalsProducer:
    """
    Polls yFinance for metals prices and publishes ticks to Kafka.

    Attributes:
        poll_interval: Seconds between polls (min 15 to avoid rate-limits).
        assets: List of metals asset configs from assets.py.
    """

    def __init__(
        self,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        assets: list[dict] | None = None,
    ) -> None:
        self.poll_interval = max(poll_interval, 15)
        self.assets = assets or [
            a for a in METALS_ASSETS
            if a["display_symbol"] in SYMBOL_TO_YF
        ]
        self._producer = None
        self._running = False
        self._tick_count = 0

    # ------------------------------------------------------------------
    # Kafka producer (lazy init)
    # ------------------------------------------------------------------

    def _get_producer(self):
        if self._producer is None:
            try:
                from kafka import KafkaProducer  # type: ignore[import]
                self._producer = KafkaProducer(**PRODUCER_CONFIG)
                logger.info(
                    "Kafka producer connected",
                    extra={"bootstrap_servers": PRODUCER_CONFIG["bootstrap_servers"]},
                )
            except Exception as exc:
                logger.error("Failed to create Kafka producer", extra={"error": str(exc)})
                raise
        return self._producer

    def _publish(self, tick: dict[str, Any]) -> None:
        try:
            producer = self._get_producer()
            payload  = json.dumps(tick)
            producer.send(
                TOPIC_MARKET_STREAM,
                key=tick["symbol"],
                value=payload,
            )
            self._tick_count += 1
            logger.info(
                "Metals tick published",
                extra={
                    "symbol": tick["symbol"],
                    "close":  tick.get("close"),
                    "total_ticks": self._tick_count,
                },
            )
        except Exception as exc:
            logger.error("Kafka publish failed", extra={"error": str(exc)})

    # ------------------------------------------------------------------
    # Main poll loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Start the polling loop. Blocks until stop() is called or a
        KeyboardInterrupt / SIGTERM is received.
        """
        self._running = True

        logger.info(
            "Starting yFinance metals producer",
            extra={
                "symbols": [a["display_symbol"] for a in self.assets],
                "poll_interval_seconds": self.poll_interval,
            },
        )

        consecutive_errors = 0
        max_consecutive_errors = 10

        while self._running:
            poll_start = time.monotonic()

            for asset in self.assets:
                if not self._running:
                    break

                display_symbol = asset["display_symbol"]
                yf_ticker      = SYMBOL_TO_YF.get(display_symbol)

                if not yf_ticker:
                    logger.warning(
                        "No yFinance mapping for symbol",
                        extra={"display_symbol": display_symbol},
                    )
                    continue

                tick = _fetch_tick(display_symbol, yf_ticker, asset)

                if tick:
                    self._publish(tick)
                    consecutive_errors = 0
                else:
                    consecutive_errors += 1
                    logger.warning(
                        "Tick fetch returned None",
                        extra={
                            "symbol": display_symbol,
                            "consecutive_errors": consecutive_errors,
                        },
                    )

            if consecutive_errors >= max_consecutive_errors:
                logger.error(
                    "Too many consecutive errors — backing off",
                    extra={"consecutive_errors": consecutive_errors},
                )
                time.sleep(min(STREAM_RECONNECT_DELAY_SECONDS * consecutive_errors, 120))

            elapsed = time.monotonic() - poll_start
            sleep_time = max(0.0, self.poll_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

        self._cleanup()

    def stop(self) -> None:
        logger.info("Stopping yFinance metals producer")
        self._running = False

    def _cleanup(self) -> None:
        if self._producer:
            try:
                self._producer.flush()
                self._producer.close()
                logger.info("Kafka producer closed cleanly")
            except Exception as exc:
                logger.warning("Error closing Kafka producer", extra={"error": str(exc)})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    producer = YFinanceMetalsProducer()

    def _handle_signal(signum, frame):
        logger.info("Shutdown signal received")
        producer.stop()

    signal.signal(signal.SIGINT,  _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    producer.run()


if __name__ == "__main__":
    main()