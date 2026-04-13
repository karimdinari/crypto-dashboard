"""
Binance WebSocket Producer
==========================
Connects to Binance public WebSocket streams for BTC/USD and ETH/USD,
receives live trade ticks (~1s), and publishes them to the Kafka topic
``market_stream``.

No API key required — Binance public streams are free and open.

Run from backend/:
    python -m app.ingestion.streaming.binance_ws_producer

Requirements (add to requirements.txt if not present):
    websocket-client>=1.7,<2
    kafka-python>=2.0,<3
"""

from __future__ import annotations

import json
import signal
import threading
import time
from datetime import datetime, timezone
from typing import Any

import websocket

from app.config.logging_config import get_logger
from app.config.settings import (
    BINANCE_WS_BASE_URL,
    STREAM_SYMBOLS,
    STREAM_RECONNECT_DELAY_SECONDS,
)
from app.ingestion.streaming.kafka_config import (
    PRODUCER_CONFIG,
    TOPIC_MARKET_STREAM,
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Binance symbol mapping
# Our symbol  →  Binance stream name
# ---------------------------------------------------------------------------

SYMBOL_MAP: dict[str, str] = {
    "BTC/USD": "btcusdt",
    "ETH/USD": "ethusdt",
}

# How many reconnect attempts before giving up (0 = infinite)
MAX_RECONNECT_ATTEMPTS = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_stream_url(symbols: list[str]) -> str:
    streams = []
    for sym in symbols:
        binance_sym = SYMBOL_MAP.get(sym)
        if binance_sym:
            streams.append(f"{binance_sym}@trade")
        else:
            logger.warning("No Binance mapping for symbol", extra={"symbol": sym})

    if not streams:
        raise ValueError("No valid Binance symbols found in STREAM_SYMBOLS")

    if len(streams) == 1:
        # single stream: wss://stream.binance.com:9443/ws/btcusdt@trade
        return f"{BINANCE_WS_BASE_URL}/{streams[0]}"

    # combined stream: wss://stream.binance.com:9443/stream?streams=btcusdt@trade/ethusdt@trade
    combined = "/".join(streams)
    base = BINANCE_WS_BASE_URL.replace("/ws", "")
    return f"{base}/stream?streams={combined}"

def _parse_trade(raw: dict[str, Any]) -> dict[str, Any] | None:
    """
    Parse a Binance @trade message into our standard tick format.

    Binance trade event fields:
        e  - event type ("trade")
        E  - event time (ms)
        s  - symbol (e.g. "BTCUSDT")
        p  - price (string)
        q  - quantity (string)
        T  - trade time (ms)

    Combined stream wraps it in {"stream": "...", "data": {...}}
    """
    # unwrap combined stream envelope if present
    if "data" in raw:
        raw = raw["data"]

    if raw.get("e") != "trade":
        return None

    binance_sym = raw.get("s", "").lower()          # e.g. "btcusdt"
    price_str   = raw.get("p")
    qty_str     = raw.get("q")
    trade_ts_ms = raw.get("T") or raw.get("E")

    if not price_str or not trade_ts_ms:
        return None

    # Reverse-map binance symbol → our display symbol
    our_symbol = next(
        (k for k, v in SYMBOL_MAP.items() if v == binance_sym),
        binance_sym.upper(),
    )

    timestamp = datetime.fromtimestamp(
        int(trade_ts_ms) / 1000, tz=timezone.utc
    ).isoformat()

    return {
        "symbol":         our_symbol,
        "market_type":    "crypto",
        "price":          float(price_str),
        "quantity":       float(qty_str) if qty_str else None,
        "source":         "binance_ws",
        "timestamp":      timestamp,
        "ingestion_time": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Producer
# ---------------------------------------------------------------------------

class BinanceWSProducer:
    """
    Connects to Binance WebSocket trade streams and publishes
    ticks to Kafka topic ``market_stream``.
    """

    def __init__(self, symbols: list[str] | None = None) -> None:
        self.symbols = symbols or STREAM_SYMBOLS
        self.url     = _build_stream_url(self.symbols)
        self._producer = None
        self._ws: websocket.WebSocketApp | None = None
        self._stop_event = threading.Event()
        self._reconnect_attempts = 0
        self._tick_count = 0

    # ------------------------------------------------------------------
    # Kafka producer (lazy init so we only connect when WS is ready)
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
            if self._tick_count % 100 == 0:
                logger.info(
                    "Ticks published",
                    extra={"count": self._tick_count, "last_symbol": tick["symbol"]},
                )
        except Exception as exc:
            logger.error("Kafka publish failed", extra={"error": str(exc)})

    # ------------------------------------------------------------------
    # WebSocket callbacks
    # ------------------------------------------------------------------

    def _on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        try:
            raw  = json.loads(message)
            tick = _parse_trade(raw)
            if tick:
                self._publish(tick)
        except Exception as exc:
            logger.warning("Failed to process message", extra={"error": str(exc)})

    def _on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        logger.error("WebSocket error", extra={"error": str(error)})

    def _on_close(
        self,
        ws: websocket.WebSocketApp,
        close_status_code: int | None,
        close_msg: str | None,
    ) -> None:
        logger.warning(
            "WebSocket closed",
            extra={"status_code": close_status_code, "message": close_msg},
        )

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        self._reconnect_attempts = 0
        logger.info(
            "WebSocket connected",
            extra={"url": self.url, "symbols": self.symbols},
        )

    # ------------------------------------------------------------------
    # Run loop with auto-reconnect
    # ------------------------------------------------------------------

    def run(self) -> None:
        logger.info(
            "Starting Binance WS producer",
            extra={"symbols": self.symbols, "url": self.url},
        )

        while not self._stop_event.is_set():
            if MAX_RECONNECT_ATTEMPTS and self._reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
                logger.error("Max reconnect attempts reached — stopping producer")
                break

            self._ws = websocket.WebSocketApp(
                self.url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )

            try:
                # run_forever blocks until the connection drops
                self._ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as exc:
                logger.error("run_forever raised", extra={"error": str(exc)})

            if self._stop_event.is_set():
                break

            self._reconnect_attempts += 1
            delay = min(
                STREAM_RECONNECT_DELAY_SECONDS * (2 ** min(self._reconnect_attempts, 6)),
                60,
            )
            logger.info(
                "Reconnecting",
                extra={
                    "attempt": self._reconnect_attempts,
                    "delay_seconds": delay,
                },
            )
            time.sleep(delay)

        self._cleanup()

    def stop(self) -> None:
        logger.info("Stopping Binance WS producer")
        self._stop_event.set()
        if self._ws:
            self._ws.close()

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
    producer = BinanceWSProducer(symbols=STREAM_SYMBOLS)

    # Graceful shutdown on SIGINT / SIGTERM
    def _handle_signal(signum, frame):
        logger.info("Shutdown signal received")
        producer.stop()

    signal.signal(signal.SIGINT,  _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    producer.run()


if __name__ == "__main__":
    main()