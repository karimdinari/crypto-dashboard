from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class SignalRowOut(BaseModel):
    """Recent signal row (UI ``Signals`` desk / Kafka + model fusion stub)."""

    asset: str
    sig: Literal["BUY", "SELL", "HOLD"]
    conf: float
    at: str
