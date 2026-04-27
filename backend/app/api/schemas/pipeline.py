from __future__ import annotations

from pydantic import BaseModel


class PipelineFileInfo(BaseModel):
    id: str
    path: str
    exists: bool
    rows: int | None
    mtime: str | None


class PipelineStatus(BaseModel):
    last_refresh: str
    generated_at: str
    files: list[PipelineFileInfo]
