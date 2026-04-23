from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.api.schemas.pipeline import PipelineFileInfo, PipelineStatus
from app.config.settings import BRONZE_PATH, GOLD_PATH, SILVER_PATH


def _mtime_iso(p: Path) -> str | None:
    if not p.is_file():
        return None
    ts = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
    return ts.isoformat().replace("+00:00", "Z")


def _row_count(p: Path) -> int | None:
    if not p.is_file():
        return None
    try:
        import pyarrow.parquet as pq

        meta = pq.ParquetFile(p).metadata
        if meta is not None:
            return int(meta.num_rows)
    except Exception:
        pass
    try:
        import pandas as pd

        return int(pd.read_parquet(p).shape[0])
    except Exception:
        return None


def traced_files() -> list[tuple[str, Path]]:
    """Stable ids the dashboard can show as Bronze / Silver / Gold health."""
    b, s, g = Path(BRONZE_PATH), Path(SILVER_PATH), Path(GOLD_PATH)
    return [
        ("bronze_crypto_prices", b / "crypto_prices" / "data.parquet"),
        ("bronze_forex_rates", b / "forex_rates" / "data.parquet"),
        ("bronze_metals_prices", b / "metals_prices" / "data.parquet"),
        ("bronze_news", b / "news" / "data.parquet"),
        ("bronze_stream_ticks", b / "stream_ticks"),
        ("bronze_stream_news", b / "stream_news"),
        ("silver_market_data", s / "market_data" / "data.parquet"),
        ("silver_crypto_data", s / "crypto_data" / "data.parquet"),
        ("silver_forex_data", s / "forex_data" / "data.parquet"),
        ("silver_metals_data", s / "metals_data" / "data.parquet"),
        ("silver_news_data", s / "news_data" / "data.parquet"),
        ("gold_market_features", g / "market_features" / "data.parquet"),
        ("gold_correlation_matrix", g / "correlation_matrix" / "data.parquet"),
        ("gold_news_aggregates", g / "news_aggregates" / "data.parquet"),
    ]


def build_pipeline_status() -> PipelineStatus:
    files: list[PipelineFileInfo] = []
    gold_mtimes: list[str] = []

    for fid, path in traced_files():
        if path.is_dir():
            exists = path.is_dir() and any(path.glob("**/*.parquet"))
            rows = None
            mtime = None
            if exists:
                newest = max((f for f in path.glob("**/*.parquet") if f.is_file()), key=lambda x: x.stat().st_mtime, default=None)
                if newest is not None:
                    mtime = _mtime_iso(newest)
        else:
            exists = path.is_file()
            rows = _row_count(path) if exists else None
            mtime = _mtime_iso(path) if exists else None
            if fid.startswith("gold") and mtime:
                gold_mtimes.append(mtime)

        files.append(
            PipelineFileInfo(
                id=fid,
                path=str(path),
                exists=exists,
                rows=rows,
                mtime=mtime,
            )
        )

    last_refresh = max(gold_mtimes) if gold_mtimes else datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")
    generated = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")

    return PipelineStatus(last_refresh=last_refresh, generated_at=generated, files=files)
