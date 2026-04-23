from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class NewsItemOut(BaseModel):
    id: str
    headline: str
    source: str
    publishedAt: str
    sentiment: Literal["positive", "neutral", "negative"]
    url: str
    symbols: list[str]
    spark: list[float]
