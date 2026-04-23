from __future__ import annotations

import asyncio
from pathlib import Path
from urllib.parse import unquote

import pandas as pd
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.schemas.market import AssetOut, StreamTickOut, OHLCVOut
from app.api.services.asset_builder import build_assets_list
from app.config.settings import SILVER_PATH
from app.ingestion.streaming.kafka_consumer import read_latest_per_symbol

router = APIRouter()


def _iso_utc(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    t = pd.to_datetime(v, utc=True, errors="coerce")
    if pd.isna(t):
        return ""
    s = t.isoformat()
    return s[:-6] + "Z" if s.endswith("+00:00") else s


def _safe_float(v, default: float = 0.0) -> float:
    x = pd.to_numeric(v, errors="coerce")
    return default if pd.isna(x) else float(x)


def _normalize_symbol(value: str) -> str:
    return value.replace("/", "").replace("_", "").replace("-", "").strip().upper()


@router.get("/assets", response_model=list[AssetOut])
def get_assets() -> list[AssetOut]:
    """
    Latest per-symbol rows from Gold ``market_features``, enriched for the dashboard.
    """
    return build_assets_list()


@router.get("/stream/latest", response_model=list[StreamTickOut])
def get_stream_latest() -> list[StreamTickOut]:
    """Latest tick per symbol from Bronze ``stream_ticks``."""
    df = read_latest_per_symbol()
    if df is None or df.empty:
        return []

    df = df.copy()
    df["_ts"] = pd.to_datetime(df.get("timestamp"), utc=True, errors="coerce")

    group_col = "display_symbol" if "display_symbol" in df.columns and df["display_symbol"].notna().any() else "symbol"
    df = df.sort_values("_ts").groupby(group_col, sort=False).last().reset_index(drop=True)

    out: list[StreamTickOut] = []
    for _, row in df.iterrows():
        sym = str(row.get("display_symbol") or row.get("symbol") or "").strip()
        if not sym:
            continue

        price = _safe_float(row.get("close", row.get("price")), 0.0)
        if price <= 0:
            continue

        out.append(
            StreamTickOut(
                symbol=sym,
                market_type=str(row.get("market_type", "unknown")),
                price=price,
                source=str(row.get("source", "")),
                timestamp=_iso_utc(row.get("timestamp")),
                ingestion_time=_iso_utc(row.get("ingestion_time")),
            )
        )
    return out


@router.get("/debug/history")
def debug_history():
    """Debug endpoint to inspect parquet contents."""
    path = Path(SILVER_PATH) / "market_data" / "data.parquet"
    return {
        "path": str(path),
        "exists": path.exists(),
        "silver_path": SILVER_PATH,
        "data": pd.read_parquet(path)[["symbol", "display_symbol"]].drop_duplicates().to_dict("records") if path.exists() else []
    }


@router.get("/history/{symbol}", response_model=list[OHLCVOut])
def get_historical_ohlcv(symbol: str) -> list[OHLCVOut]:
    """OHLCV history for a given symbol. Accepts BTCUSD, BTC-USD, BTC_USD, BTC/USD."""
    path = Path(SILVER_PATH) / "market_data" / "data.parquet"
    if not path.exists():
        return []

    df = pd.read_parquet(path)
    if df.empty:
        return []

    sym = unquote(symbol).strip()
    sym_norm = sym.replace("/", "").replace("_", "").replace("-", "").strip().upper()

    df = df.copy()
    df["symbol"] = df["symbol"].astype(str)
    df["display_symbol"] = df["display_symbol"].astype(str)

    df = df[
        (df["display_symbol"].str.upper() == sym.upper())
        | (df["symbol"].str.upper() == sym.upper())
        | (df["display_symbol"].str.replace("/", "", regex=False).str.upper() == sym_norm)
        | (df["symbol"].str.replace("/", "", regex=False).str.upper() == sym_norm)
    ]

    if df.empty:
        return []

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.sort_values("timestamp")

    out = []
    for _, row in df.iterrows():
        vol = float(row.get("volume", 0) or 0)
        out.append(
            OHLCVOut(
                t=_iso_utc(row.get("timestamp")),
                o=float(row.get("open", 0) or 0),
                h=float(row.get("high", 0) or 0),
                l=float(row.get("low", 0) or 0),
                c=float(row.get("close", 0) or 0),
                v=vol if pd.notna(vol) else 0.0,
            )
        )
    return out


@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            df = read_latest_per_symbol()
            ticks = []

            if df is not None and not df.empty:
                df = df.copy()
                df["_ts"] = pd.to_datetime(df.get("timestamp"), utc=True, errors="coerce")

                group_col = "display_symbol" if "display_symbol" in df.columns and df["display_symbol"].notna().any() else "symbol"
                df = df.sort_values("_ts").groupby(group_col, sort=False).last().reset_index(drop=True)

                for _, row in df.iterrows():
                    sym = str(row.get("display_symbol") or row.get("symbol") or "").strip()
                    if not sym:
                        continue

                    price = _safe_float(row.get("close", row.get("price")), 0.0)
                    if price <= 0:
                        continue

                    ticks.append(
                        {
                            "symbol": sym,
                            "market_type": str(row.get("market_type", "unknown")),
                            "price": price,
                            "source": str(row.get("source", "")),
                            "timestamp": _iso_utc(row.get("timestamp")),
                            "ingestion_time": _iso_utc(row.get("ingestion_time")),
                        }
                    )

            if ticks:
                await websocket.send_json(ticks)

            await asyncio.sleep(2.0)

    except WebSocketDisconnect:
        pass