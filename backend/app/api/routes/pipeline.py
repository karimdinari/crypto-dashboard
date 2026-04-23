from __future__ import annotations

from fastapi import APIRouter

from app.api.schemas.pipeline import PipelineStatus
from app.api.services.pipeline_status import build_pipeline_status

router = APIRouter()


@router.get("/pipeline", response_model=PipelineStatus)
def get_pipeline() -> PipelineStatus:
    """Lakehouse file inventory for the Pipeline Monitoring page."""
    return build_pipeline_status()
