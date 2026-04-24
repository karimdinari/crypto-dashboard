from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.api.schemas.signal import SignalRowOut
from app.api.services.asset_builder import build_assets_list

router = APIRouter()


@router.get("/signals/recent", response_model=list[SignalRowOut])
def recent_signals() -> list[SignalRowOut]:
    """
    Compact signal feed for the Signals desk UI.

    Rows are derived from the latest asset snapshot (swap for Kafka / model events later).
    """
    now = datetime.now(tz=timezone.utc).strftime("%H:%M UTC")
    out: list[SignalRowOut] = []
    for a in build_assets_list():
        out.append(
            SignalRowOut(
                asset=a.symbol,
                sig=a.prediction,
                conf=round(a.confidence, 2),
                at=now,
            )
        )
    return out
