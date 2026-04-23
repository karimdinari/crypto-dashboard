from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class PredictionRowOut(BaseModel):
    """Per-asset ML-style output for dedicated predictions endpoints."""

    symbol: str
    market: Literal["crypto", "forex", "metals"]
    prediction: Literal["BUY", "SELL", "HOLD"]
    confidence: float
    probUp: float
    probDown: float
    modelVersion: str
