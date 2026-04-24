from __future__ import annotations

import math
from typing import Literal

import pandas as pd
from pathlib import Path
from fastapi import APIRouter, Query

from app.api.schemas.news import NewsItemOut
from app.ingestion.streaming.news_kafka_consumer import read_all_news
from app.config.settings import SILVER_PATH

router = APIRouter()


def _safe_float(v, default: float = 0.0) -> float:
    x = pd.to_numeric(v, errors="coerce")
    return default if pd.isna(x) else float(x)


def _iso_utc(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    t = pd.to_datetime(v, utc=True, errors="coerce")
    if pd.isna(t):
        return ""
    s = t.isoformat()
    return s[:-6] + "Z" if s.endswith("+00:00") else s


def _normalize_symbol(value: str) -> str:
    return str(value).replace("/", "").replace("_", "").replace("-", "").strip().upper()


def _safe_sentiment(label: str | None) -> Literal["positive", "neutral", "negative"]:
    value = str(label or "neutral").strip().lower()
    if value not in {"positive", "neutral", "negative"}:
        return "neutral"
    return value  # type: ignore[return-value]


def _spark_from_compound(compound: float) -> list[float]:
    c = max(-1.0, min(1.0, _safe_float(compound)))
    return [round(c + 0.12 * math.sin(i * 0.7), 4) for i in range(7)]


def _build_news_items(df: pd.DataFrame, limit: int) -> list[NewsItemOut]:
    if df.empty:
        return []

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.sort_values("timestamp", ascending=False).head(limit)

    items: list[NewsItemOut] = []
    for _, row in df.iterrows():
        sym = str(row.get("display_symbol") or row.get("symbol") or "").strip()

        items.append(
            NewsItemOut(
                id=str(row.get("news_id", row.get("url", "")))[:80],
                headline=str(row.get("title", "")),
                source=str(row.get("source_name") or row.get("source", "unknown")),
                publishedAt=_iso_utc(row.get("timestamp")),
                sentiment=_safe_sentiment(row.get("sentiment_label")),
                url=str(row.get("url", "#")),
                symbols=[sym] if sym else [],
                spark=_spark_from_compound(row.get("sentiment_compound", 0)),
            )
        )
    return items


@router.get("/news", response_model=list[NewsItemOut])
def get_news(
    symbol: str | None = Query(None, description="Filter by raw symbol, e.g. BTCUSD"),
    limit: int = Query(100, ge=1, le=500),
) -> list[NewsItemOut]:
    df = read_all_news()
    if df.empty:
        return []

    if symbol:
        sym_norm = _normalize_symbol(symbol)

        df = df.copy()
        df["symbol"] = df.get("symbol", "").astype(str)
        df["display_symbol"] = df.get("display_symbol", "").astype(str)

        df = df[
            (df["symbol"].map(_normalize_symbol) == sym_norm)
            | (df["display_symbol"].map(_normalize_symbol) == sym_norm)
        ]

    return _build_news_items(df, limit)


from pathlib import Path

from app.config.settings import SILVER_PATH


@router.get("/news/history/{symbol}", response_model=list[NewsItemOut])
def get_news_history(
    symbol: str,
    limit: int = Query(200, ge=1, le=1000),
) -> list[NewsItemOut]:
    """
    Historical news for one asset, read from Silver parquet.
    Accepts:
    BTCUSD, ETHUSD, EURUSD, GBPUSD, XAUUSD, XAGUSD
    """
    path = Path(SILVER_PATH) / "news_data" / "data.parquet"
    if not path.exists():
        return []

    df = pd.read_parquet(path)
    if df.empty:
        return []

    sym_norm = _normalize_symbol(symbol)

    df = df.copy()
    df["symbol"] = df.get("symbol", "").astype(str)
    df["display_symbol"] = df.get("display_symbol", "").astype(str)

    df = df[
        (df["symbol"].map(_normalize_symbol) == sym_norm)
        | (df["display_symbol"].map(_normalize_symbol) == sym_norm)
    ]

    return _build_news_items(df, limit)