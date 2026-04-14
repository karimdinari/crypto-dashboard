from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import websocket
from dotenv import load_dotenv
from kafka import KafkaProducer

from app.config.logging_config import get_logger
from app.ingestion.streaming.kafka_config import (
    PRODUCER_CONFIG,
    TOPIC_MARKET_STREAM,
)

load_dotenv()

logger = get_logger(__name__)

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FINNHUB_WS_URL = f"wss://ws.finnhub.io?token={FINNHUB_API_KEY}"

# Adjust symbols if needed depending on your Finnhub account/data format
FOREX_SYMBOLS = [
    "OANDA:EUR_USD",
    "OANDA:GBP_USD",
]

producer = KafkaProducer(**PRODUCER_CONFIG)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_display_symbol(raw_symbol: str) -> tuple[str, str]:
    """
    Example:
        OANDA:EUR_USD -> ('EURUSD', 'EUR/USD')
    """
    symbol_part = raw_symbol.split(":")[-1]
    display_symbol = symbol_part.replace("_", "/")
    symbol = symbol_part.replace("_", "")
    return symbol, display_symbol


def publish_event(event: dict) -> None:
    """
    Your current kafka_config expects a string/bytes payload,
    so we serialize dict -> JSON string here before send().
    """
    payload = json.dumps(event)
    producer.send(TOPIC_MARKET_STREAM, value=payload, key=event["symbol"])
    producer.flush()


def on_open(ws) -> None:
    logger.info("Connected to Finnhub WebSocket")

    for symbol in FOREX_SYMBOLS:
        subscribe_message = {
            "type": "subscribe",
            "symbol": symbol,
        }
        ws.send(json.dumps(subscribe_message))
        logger.info(f"Subscribed to Finnhub symbol: {symbol}")


def on_message(ws, message: str) -> None:
    try:
        payload = json.loads(message)

        # Finnhub sends various message types; trade is the main one
        if payload.get("type") != "trade":
            return

        data = payload.get("data", [])
        if not data:
            return

        for item in data:
            raw_symbol = item.get("s")
            price = item.get("p")
            timestamp_ms = item.get("t")

            if raw_symbol is None or price is None or timestamp_ms is None:
                continue

            symbol, display_symbol = normalize_display_symbol(raw_symbol)

            event = {
                "symbol": symbol,
                "display_symbol": display_symbol,
                "market_type": "forex",
                "event_time": datetime.fromtimestamp(
                    timestamp_ms / 1000,
                    tz=timezone.utc,
                ).isoformat(),
                "price": float(price),
                "source": "finnhub_ws",
                "ingestion_time": utc_now_iso(),
            }

            publish_event(event)
            logger.info(
                "Published Finnhub forex event",
                extra={
                    "symbol": event["symbol"],
                    "display_symbol": event["display_symbol"],
                    "price": event["price"],
                    "source": event["source"],
                },
            )

    except Exception as exc:
        logger.exception(f"Error processing Finnhub message: {exc}")


def on_error(ws, error) -> None:
    logger.error(f"Finnhub WebSocket error: {error}")


def on_close(ws, close_status_code, close_msg) -> None:
    logger.warning(
        f"Finnhub WebSocket closed: code={close_status_code}, msg={close_msg}"
    )


def run() -> None:
    if not FINNHUB_API_KEY:
        raise ValueError("FINNHUB_API_KEY is missing in .env")

    ws = websocket.WebSocketApp(
        FINNHUB_WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    logger.info("Starting Finnhub WebSocket producer")
    ws.run_forever()


if __name__ == "__main__":
    run()