"""
Finnhub News WebSocket Producer
================================
Connects to the Finnhub WebSocket feed, receives real-time news events,
filters them against NEWS_TARGETS keywords, and publishes matching articles
to the Kafka topic ``news_stream``.

Finnhub's free-tier WS pushes general news events (type: "news") alongside
trade ticks. We subscribe to all NEWS_TARGETS symbols and capture any
headline that matches our keyword list.

Run from backend/:
    python -m app.ingestion.streaming.finnhub_news_ws_producer

Requirements (already in requirements.txt):
    websocket-client>=1.7,<2
    kafka-python>=2.0,<3
"""

from __future__ import annotations

import hashlib
import json
import signal
import time
from datetime import datetime, timezone
from typing import Any

import websocket

from app.config.assets import NEWS_TARGETS
from app.config.logging_config import get_logger
from app.config.settings import FINNHUB_API_KEY, STREAM_RECONNECT_DELAY_SECONDS
from app.ingestion.streaming.kafka_config import (
    PRODUCER_CONFIG,
    TOPIC_NEWS_STREAM,
)

logger = get_logger(__name__)

FINNHUB_WS_URL = f"wss://ws.finnhub.io?token={FINNHUB_API_KEY}"

# Symbols to subscribe to on the Finnhub WS
# Finnhub news WS uses equity/forex tickers — we subscribe to the ones
# relevant to our assets so Finnhub filters server-side where possible.
_WS_SUBSCRIPTIONS: list[str] = [
    "BINANCE:BTCUSDT",
    "BINANCE:ETHUSDT",
    "OANDA:EUR_USD",
    "OANDA:GBP_USD",
]

# Max reconnect attempts (0 = infinite)
MAX_RECONNECT_ATTEMPTS = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_news_id(title: str, timestamp: int) -> str:
    """Stable dedup key — same logic as the batch ingestor."""
    return hashlib.md5(f"{title}|{timestamp}".encode()).hexdigest()


def _keyword_match(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def _match_targets(headline: str, summary: str) -> list[dict]:
    """Return all NEWS_TARGETS whose keywords match this article."""
    combined = f"{headline} {summary}".lower()
    return [t for t in NEWS_TARGETS if _keyword_match(combined, t["keywords"])]


def _build_news_event(
    item: dict[str, Any],
    target: dict,
    ingestion_time: str,
) -> dict[str, Any]:
    """Build a Bronze-ready news event from a raw Finnhub WS message."""
    headline = str(item.get("headline", ""))
    summary = str(item.get("summary", ""))
    unix_ts = int(item.get("datetime", 0))

    news_id = _make_news_id(headline, unix_ts)
    timestamp = (
        datetime.fromtimestamp(unix_ts, tz=timezone.utc).isoformat()
        if unix_ts
        else ingestion_time
    )

    return {
        "symbol": target["symbol"],
        "display_symbol": target["display_symbol"],
        "market_type": target["market_type"],
        "source": "finnhub_ws",
        "news_id": news_id,
        "timestamp": timestamp,
        "title": headline,
        "summary": summary[:1000],
        "url": str(item.get("url", "")),
        "source_name": str(item.get("source", "")),
        "ingestion_time": ingestion_time,
    }


# ---------------------------------------------------------------------------
# Producer
# ---------------------------------------------------------------------------

class FinnhubNewsWSProducer:
    """
    Connects to the Finnhub WebSocket and publishes matching news events
    to the Kafka ``news_stream`` topic.

    Each article is matched against all NEWS_TARGETS. If it matches
    multiple targets (e.g. a BTC/ETH joint article), one event is
    published per matching target so downstream consumers can filter
    by symbol independently.
    """

    def __init__(self) -> None:
        if not FINNHUB_API_KEY:
            raise ValueError(
                "FINNHUB_API_KEY is not set. Add it to backend/.env"
            )

        self._producer = None
        self._ws: websocket.WebSocketApp | None = None
        self._stop_event = False
        self._reconnect_attempts = 0
        self._published_count = 0
        # Dedup within a session to avoid republishing the same article
        # if the WS reconnects mid-stream.
        self._seen_ids: set[str] = set()

    # ------------------------------------------------------------------
    # Kafka producer (lazy init)
    # ------------------------------------------------------------------

    def _get_producer(self):
        if self._producer is None:
            from kafka import KafkaProducer  # type: ignore[import]
            self._producer = KafkaProducer(**PRODUCER_CONFIG)
            logger.info(
                "Kafka news producer connected",
                extra={"bootstrap_servers": PRODUCER_CONFIG["bootstrap_servers"]},
            )
        return self._producer

    def _publish(self, event: dict[str, Any]) -> None:
        try:
            producer = self._get_producer()
            payload = json.dumps(event)
            producer.send(
                TOPIC_NEWS_STREAM,
                key=event["symbol"],
                value=payload,
            )
            self._published_count += 1
            logger.info(
                "News event published",
                extra={
                    "symbol": event["symbol"],
                    "title": event["title"][:80],
                    "total_published": self._published_count,
                },
            )
        except Exception as exc:
            logger.error("Kafka publish failed", extra={"error": str(exc)})

    # ------------------------------------------------------------------
    # WebSocket callbacks
    # ------------------------------------------------------------------

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        self._reconnect_attempts = 0
        logger.info("Finnhub news WS connected")

        # Subscribe to symbols — Finnhub will push related news events
        for sym in _WS_SUBSCRIPTIONS:
            ws.send(json.dumps({"type": "subscribe", "symbol": sym}))
            logger.info("Subscribed to Finnhub symbol", extra={"symbol": sym})

    def _on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        try:
            payload = json.loads(message)
        except Exception as exc:
            logger.warning("Failed to parse WS message", extra={"error": str(exc)})
            return

        msg_type = payload.get("type")

        # Finnhub sends {"type": "news", "data": [{...}, ...]}
        if msg_type != "news":
            return

        ingestion_time = datetime.now(timezone.utc).isoformat()
        articles = payload.get("data", [])
        if not isinstance(articles, list):
            articles = [payload.get("data", {})]

        for item in articles:
            if not isinstance(item, dict):
                continue

            headline = str(item.get("headline", ""))
            summary = str(item.get("summary", ""))
            unix_ts = int(item.get("datetime", 0))
            news_id = _make_news_id(headline, unix_ts)

            if news_id in self._seen_ids:
                continue
            self._seen_ids.add(news_id)

            matched_targets = _match_targets(headline, summary)
            if not matched_targets:
                logger.debug(
                    "News article matched no targets — skipping",
                    extra={"headline": headline[:80]},
                )
                continue

            for target in matched_targets:
                event = _build_news_event(item, target, ingestion_time)
                self._publish(event)

    def _on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        logger.error("Finnhub news WS error", extra={"error": str(error)})

    def _on_close(
        self,
        ws: websocket.WebSocketApp,
        close_status_code: int | None,
        close_msg: str | None,
    ) -> None:
        logger.warning(
            "Finnhub news WS closed",
            extra={"status_code": close_status_code, "message": close_msg},
        )

    # ------------------------------------------------------------------
    # Run loop with auto-reconnect
    # ------------------------------------------------------------------

    def run(self) -> None:
        logger.info("Starting Finnhub news WS producer")

        while not self._stop_event:
            if MAX_RECONNECT_ATTEMPTS and self._reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
                logger.error("Max reconnect attempts reached — stopping")
                break

            self._ws = websocket.WebSocketApp(
                FINNHUB_WS_URL,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )

            try:
                self._ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as exc:
                logger.error("run_forever raised", extra={"error": str(exc)})

            if self._stop_event:
                break

            self._reconnect_attempts += 1
            delay = min(
                STREAM_RECONNECT_DELAY_SECONDS * (2 ** min(self._reconnect_attempts, 6)),
                60,
            )
            logger.info(
                "Reconnecting news WS",
                extra={"attempt": self._reconnect_attempts, "delay_seconds": delay},
            )
            time.sleep(delay)

        self._cleanup()

    def stop(self) -> None:
        logger.info("Stopping Finnhub news WS producer")
        self._stop_event = True
        if self._ws:
            self._ws.close()

    def _cleanup(self) -> None:
        if self._producer:
            try:
                self._producer.flush()
                self._producer.close()
                logger.info("Kafka news producer closed cleanly")
            except Exception as exc:
                logger.warning("Error closing Kafka producer", extra={"error": str(exc)})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    producer = FinnhubNewsWSProducer()

    def _handle_signal(signum, frame):
        logger.info("Shutdown signal received")
        producer.stop()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    producer.run()


if __name__ == "__main__":
    main()
