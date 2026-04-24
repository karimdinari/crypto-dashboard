"""
Finnhub News Polling Producer
==============================
Every 10 minutes, fetches the latest articles from Finnhub REST API,
takes only the NEW ones (not seen before), publishes them to Kafka
``news_stream`` topic — simulating a real-time news stream.

Replaces finnhub_news_ws_producer.py (WS is unreliable on free tier).

Run from backend/:
    python -m app.ingestion.streaming.finnhub_news_poll_producer
"""

from __future__ import annotations

import hashlib
import json
import signal
import time
from datetime import datetime, timezone
from typing import Any

import requests

from app.config.assets import NEWS_TARGETS
from app.config.logging_config import get_logger
from app.config.settings import (
    FINNHUB_API_KEY,
    FINNHUB_BASE_URL,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
)
from app.ingestion.streaming.kafka_config import (
    PRODUCER_CONFIG,
    TOPIC_NEWS_STREAM,
)

logger = get_logger(__name__)

POLL_INTERVAL_SECONDS = 10 * 60   # 10 minutes
MAX_ARTICLES_PER_POLL = 5         # only publish the 5 latest per poll
NEWS_CATEGORIES = ["general", "crypto", "forex"]


def _make_news_id(title: str, timestamp: int) -> str:
    return hashlib.md5(f"{title}|{timestamp}".encode()).hexdigest()


def _keyword_match(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def _fetch_category(category: str) -> list[dict]:
    """Fetch latest articles for one Finnhub category."""
    try:
        resp = requests.get(
            f"{FINNHUB_BASE_URL}/news",
            params={"category": category, "token": FINNHUB_API_KEY},
            timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []
    except Exception as exc:
        logger.warning("Finnhub fetch failed", extra={"category": category, "error": str(exc)})
        return []


class FinnhubNewsPollProducer:
    """
    Polls Finnhub REST API every POLL_INTERVAL_SECONDS.
    Publishes up to MAX_ARTICLES_PER_POLL new articles to Kafka news_stream.
    Tracks seen news_ids so no article is published twice.
    """

    def __init__(
        self,
        poll_interval: int = POLL_INTERVAL_SECONDS,
        max_articles: int = MAX_ARTICLES_PER_POLL,
    ) -> None:
        self.poll_interval = poll_interval
        self.max_articles = max_articles
        self._producer = None
        self._running = False
        self._seen_ids: set[str] = set()
        self._total_published = 0

        if not FINNHUB_API_KEY:
            raise ValueError("FINNHUB_API_KEY not set in .env")

    def _get_producer(self):
        if self._producer is None:
            from kafka import KafkaProducer  # type: ignore[import]
            self._producer = KafkaProducer(**PRODUCER_CONFIG)
            logger.info("Kafka producer connected")
        return self._producer

    def _publish(self, event: dict[str, Any]) -> None:
        try:
            self._get_producer().send(
                TOPIC_NEWS_STREAM,
                key=event["symbol"],
                value=json.dumps(event),
            )
            self._total_published += 1
            logger.info(
                "News article published",
                extra={
                    "symbol": event["symbol"],
                    "title": event["title"][:80],
                    "total_published": self._total_published,
                },
            )
        except Exception as exc:
            logger.error("Kafka publish failed", extra={"error": str(exc)})

    def _poll_once(self) -> None:
        """One poll cycle — fetch, match, publish up to max_articles new ones."""
        logger.info("Polling Finnhub for latest news")

        # collect all articles across categories, deduplicated
        all_articles: list[dict] = []
        seen_in_batch: set[str] = set()

        for category in NEWS_CATEGORIES:
            for item in _fetch_category(category):
                if not isinstance(item, dict):
                    continue
                title = str(item.get("headline", ""))
                unix_ts = int(item.get("datetime", 0))
                news_id = _make_news_id(title, unix_ts)
                if news_id not in seen_in_batch:
                    seen_in_batch.add(news_id)
                    all_articles.append(item)

        # sort by datetime descending → freshest first
        all_articles.sort(key=lambda x: int(x.get("datetime", 0)), reverse=True)

        ingestion_time = datetime.now(timezone.utc).isoformat()
        published_this_poll = 0

        for item in all_articles:
            if published_this_poll >= self.max_articles:
                break

            title = str(item.get("headline", ""))
            unix_ts = int(item.get("datetime", 0))
            news_id = _make_news_id(title, unix_ts)

            # skip already published
            if news_id in self._seen_ids:
                continue

            # match against our symbols
            summary = str(item.get("summary", ""))
            combined = f"{title} {summary}"

            for target in NEWS_TARGETS:
                if _keyword_match(combined, target["keywords"]):
                    timestamp = (
                        datetime.fromtimestamp(unix_ts, tz=timezone.utc).isoformat()
                        if unix_ts else ingestion_time
                    )
                    event = {
                        "symbol":         target["symbol"],
                        "display_symbol": target["display_symbol"],
                        "market_type":    target["market_type"],
                        "source":         "finnhub_poll",
                        "news_id":        news_id,
                        "timestamp":      timestamp,
                        "title":          title,
                        "summary":        summary[:1000],
                        "url":            str(item.get("url", "")),
                        "source_name":    str(item.get("source", "")),
                        "ingestion_time": ingestion_time,
                    }
                    self._publish(event)
                    published_this_poll += 1
                    break  # one event per article max

            self._seen_ids.add(news_id)

            if published_this_poll >= self.max_articles:
                break

        logger.info(
            "Poll complete",
            extra={
                "published_this_poll": published_this_poll,
                "total_published": self._total_published,
                "next_poll_in_seconds": self.poll_interval,
            },
        )

    def run(self) -> None:
        self._running = True
        logger.info(
            "Starting Finnhub news poll producer",
            extra={
                "poll_interval_seconds": self.poll_interval,
                "max_articles_per_poll": self.max_articles,
            },
        )

        while self._running:
            try:
                self._poll_once()
            except Exception as exc:
                logger.error("Poll error", extra={"error": str(exc)})

            # wait poll_interval but check _running every second for fast shutdown
            for _ in range(self.poll_interval):
                if not self._running:
                    break
                time.sleep(1)

        self._cleanup()

    def stop(self) -> None:
        logger.info("Stopping Finnhub news poll producer")
        self._running = False

    def _cleanup(self) -> None:
        if self._producer:
            try:
                self._producer.flush()
                self._producer.close()
                logger.info("Kafka producer closed cleanly")
            except Exception as exc:
                logger.warning("Error closing producer", extra={"error": str(exc)})


def main() -> None:
    producer = FinnhubNewsPollProducer()

    def _handle_signal(signum, frame):
        producer.stop()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    producer.run()


if __name__ == "__main__":
    main()
