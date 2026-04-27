from __future__ import annotations

from fastapi import APIRouter

from app.api.schemas.prediction import PredictionRowOut
from app.api.services.asset_builder import build_assets_list

router = APIRouter()


@router.get("/predictions", response_model=list[PredictionRowOut])
def list_predictions() -> list[PredictionRowOut]:
    """Per-asset prediction summary (same engine as embedded in ``/api/assets``)."""
    return [
        PredictionRowOut(
            symbol=a.symbol,
            market=a.market,
            prediction=a.prediction,
            confidence=a.confidence,
            probUp=a.probUp,
            probDown=a.probDown,
            modelVersion=a.modelVersion,
        )
        for a in build_assets_list()
    ]
