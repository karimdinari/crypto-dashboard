from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TopFeatureOut(BaseModel):
    name: str
    weight: float


class AssetOut(BaseModel):
    """Shape aligned with the React ``Asset`` type (``frontend/src/types.ts``)."""

    symbol: str
    name: str
    market: Literal["crypto", "forex", "metals"]
    price: float
    changePct: float = Field(description="Percent change for the latest bar, e.g. 2.34 means +2.34%")
    volume: str
    rsi: float
    macd: float
    macdSignal: float
    volatility: float
    ma7: float
    ma30: float
    ma20: float
    ma50: float
    prediction: Literal["BUY", "SELL", "HOLD"]
    confidence: float
    sentimentScore: float
    newsCount24h: int
    lastReturn: float
    anomalies: list[str]
    topFeatures: list[TopFeatureOut]
    modelVersion: str
    probUp: float
    probDown: float


class StreamTickOut(BaseModel):
    """Latest Kafka-backed tick row for ``GET /api/stream/latest``."""

    symbol: str
    market_type: str
    price: float
    source: str
    timestamp: str
    ingestion_time: str

class OHLCVOut(BaseModel):
    """Historical OHLCV for chart rendering."""
    t: str
    o: float
    h: float
    l: float
    c: float
    v: float

