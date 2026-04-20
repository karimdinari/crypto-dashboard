from __future__ import annotations

"""
Finnhub News Ingestor
=====================
Fetches financial news from the Finnhub API for all symbols defined
in NEWS_TARGETS (assets.py) and writes them to the Bronze layer.

Free-tier fix: the /news endpoint does NOT support `from`/`to` date
parameters on the free plan — passing them returns an empty list.
We fetch the latest batch per category without date filtering, then
apply a lookback filter locally using the article's `datetime` field.

Default lookback is **1 day** so scheduled daily runs only keep very recent
articles (append to Bronze; duplicates removed by `news_id` on append).
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import hashlib
import pandas as pd

from app.config.logging_config import get_logger
from app.config.settings import (
    FINNHUB_API_KEY,
    FINNHUB_BASE_URL,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    DEFAULT_RETRY_COUNT,
    DEFAULT_RETRY_BACKOFF_SECONDS,
)
from app.config.assets import NEWS_TARGETS
from app.ingestion.batch.base_ingestor import BaseIngestor
from app.etl.bronze.write_bronze import write_bronze_table

logger = get_logger(__name__)

_DEFAULT_LOOKBACK_DAYS = 1

# Finnhub general news categories to query
_NEWS_CATEGORIES = ["general", "forex", "crypto", "merger"]


def _make_news_id(title: str, timestamp: int) -> str:
    """Stable dedup key from title + unix timestamp."""
    raw = f"{title}|{timestamp}"
    return hashlib.md5(raw.encode()).hexdigest()


def _keyword_match(text: str, keywords: list[str]) -> bool:
    """Case-insensitive keyword filter."""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


class FinnhubNewsIngestor(BaseIngestor):
    """
    Fetches news from Finnhub for each NEWS_TARGET symbol and
    writes a combined Bronze news table.

    Free-tier compatible: fetches without date range params,
    filters locally by lookback_days using article datetime field.
    """

    def __init__(
        self,
        lookback_days: int = _DEFAULT_LOOKBACK_DAYS,
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(source_name="finnhub")
        self.api_key = api_key or FINNHUB_API_KEY
        self.lookback_days = lookback_days

        if not self.api_key:
            logger.warning(
                "FINNHUB_API_KEY is not set — requests will likely be rejected. "
                "Add it to backend/.env"
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(self) -> pd.DataFrame:
        """
        Fetch news for all NEWS_TARGETS.
        Returns a combined DataFrame ready for Bronze.
        """
        raw_articles = self._fetch_all_categories()

        if not raw_articles:
            logger.warning(
                "No raw articles returned from Finnhub — "
                "check API key and quota."
            )
            return pd.DataFrame()

        frames: list[pd.DataFrame] = []
        for target in NEWS_TARGETS:
            df = self._filter_for_target(raw_articles, target)
            if not df.empty:
                frames.append(df)
                self.logger.info(
                    "News articles matched",
                    extra={
                        "symbol": target["display_symbol"],
                        "articles": len(df),
                    },
                )
            else:
                logger.warning(
                    "No news matched for symbol",
                    extra={"symbol": target["display_symbol"]},
                )

        if not frames:
            logger.warning(
                "No news articles matched any symbol — "
                "keywords may be too restrictive or articles are older "
                f"than {self.lookback_days} days."
            )
            return pd.DataFrame()

        combined = pd.concat(frames, ignore_index=True)
        combined = combined.drop_duplicates(
            subset=["symbol", "news_id"], keep="first"
        )

        self.logger.info(
            "Finnhub news ingestion complete",
            extra={"total_rows": len(combined)},
        )
        return combined

    def ingest(self, mode: str = "append") -> None:
        """Fetch → write to Bronze news table."""
        df = self.fetch()
        if df.empty:
            self.logger.warning("Nothing to write — skipping Bronze write.")
            return
        write_bronze_table(df, dataset_name="news", mode=mode)  # type: ignore[arg-type]
        self.logger.info(
            "News written to Bronze",
            extra={"rows": len(df), "mode": mode},
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _cutoff_unix(self) -> int:
        """Unix timestamp for (now - lookback_days)."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.lookback_days)
        return int(cutoff.timestamp())

    def _fetch_all_categories(self) -> list[dict[str, Any]]:
        """
        Pull latest news from every Finnhub category.

        KEY FIX: free-tier /news does NOT accept `from`/`to` params —
        omit them entirely and filter locally by article datetime.
        """
        cutoff = self._cutoff_unix()
        seen_ids: set[str] = set()
        articles: list[dict[str, Any]] = []

        for category in _NEWS_CATEGORIES:
            url = f"{FINNHUB_BASE_URL}/news"
            # ✅ No `from`/`to` — free tier ignores/rejects them silently
            params: dict[str, Any] = {
                "category": category,
                "token": self.api_key,
            }
            try:
                raw = self.get_json(url, params=params)
            except Exception as exc:
                logger.warning(
                    "Finnhub request failed",
                    extra={"category": category, "error": str(exc)},
                )
                continue

            if not isinstance(raw, list):
                logger.warning(
                    "Unexpected Finnhub response type",
                    extra={"category": category, "type": type(raw).__name__},
                )
                continue

            before = len(articles)
            for item in raw:
                if not isinstance(item, dict):
                    continue

                # ✅ Local lookback filter
                article_ts = int(item.get("datetime", 0))
                if article_ts and article_ts < cutoff:
                    continue

                fid = str(item.get("id", "")) or _make_news_id(
                    str(item.get("headline", "")), article_ts
                )
                if fid in seen_ids:
                    continue
                seen_ids.add(fid)
                articles.append(item)

            added = len(articles) - before
            self.logger.info(
                "Finnhub category fetched",
                extra={"category": category, "new_articles": added},
            )

        self.logger.info(
            "Raw Finnhub articles fetched",
            extra={"count": len(articles)},
        )
        return articles

    def _filter_for_target(
        self, articles: list[dict[str, Any]], target: dict
    ) -> pd.DataFrame:
        """
        Filter articles by keyword list and build a Bronze-ready DataFrame.
        """
        keywords: list[str] = target["keywords"]
        display_symbol: str = target["display_symbol"]
        symbol: str = target["symbol"]
        market_type: str = target["market_type"]

        rows: list[dict[str, Any]] = []
        ingestion_time = self.get_ingestion_time().isoformat()

        for item in articles:
            headline = str(item.get("headline", ""))
            summary = str(item.get("summary", ""))
            combined_text = f"{headline} {summary}"

            if not _keyword_match(combined_text, keywords):
                continue

            unix_ts: int = int(item.get("datetime", 0))
            news_id = _make_news_id(headline, unix_ts)

            timestamp = (
                datetime.fromtimestamp(unix_ts, tz=timezone.utc).isoformat()
                if unix_ts
                else None
            )

            rows.append(
                {
                    "symbol": symbol,
                    "display_symbol": display_symbol,
                    "market_type": market_type,
                    "source": self.source_name,
                    "news_id": news_id,
                    "timestamp": timestamp,
                    "title": headline,
                    "summary": summary[:1000],
                    "url": str(item.get("url", "")),
                    "source_name": str(item.get("source", "")),
                    "ingestion_time": ingestion_time,
                }
            )

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        return df


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    ingestor = FinnhubNewsIngestor(lookback_days=_DEFAULT_LOOKBACK_DAYS)
    ingestor.ingest(mode="append")