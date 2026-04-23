"""
Market Analytics Terminal — FastAPI application entry.

Run from ``crypto-dashboard/backend``::

    python -m app.api.main

Or with uvicorn directly::

    uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import markets, news, pipeline, predictions, signals

app = FastAPI(
    title="Market Analytics Terminal API",
    version="0.1.0",
    description="Dashboard API over Bronze / Silver / Gold Parquet + Kafka stream ticks.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(markets.router, prefix="/api", tags=["markets"])
app.include_router(news.router, prefix="/api", tags=["news"])
app.include_router(pipeline.router, prefix="/api", tags=["pipeline"])
app.include_router(predictions.router, prefix="/api", tags=["predictions"])
app.include_router(signals.router, prefix="/api", tags=["signals"])


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
