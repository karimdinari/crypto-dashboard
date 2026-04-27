from __future__ import annotations

import pandas as pd
from pathlib import Path
from fastapi import APIRouter

from app.config.settings import GOLD_PATH

router = APIRouter()

GOLD_CORR_PATH = Path(GOLD_PATH) / "correlation_matrix" / "data.parquet"


@router.get("/correlations")
def get_correlations():
    if not GOLD_CORR_PATH.exists():
        return []

    df = pd.read_parquet(GOLD_CORR_PATH)
    if df.empty:
        return []

    return df.to_dict(orient="records")