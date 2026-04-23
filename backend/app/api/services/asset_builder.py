from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.api.schemas.market import AssetOut, TopFeatureOut
from app.api.services import lakehouse
from app.config.settings import GOLD_PATH
from app.serving.signal_engine import signal_from_features, top_features_from_row

_NAME = lakehouse._display_to_name()
_MARKET = lakehouse._display_to_market()


def _news_counts_for_assets() -> dict[str, int]:
    """
    Prefer Gold ``news_aggregates`` (no FinBERT import). Falls back to empty dict.
    """
    p = Path(GOLD_PATH) / "news_aggregates" / "data.parquet"
    if not p.is_file():
        return {}
    try:
        df = pd.read_parquet(p)
    except Exception:
        return {}
    if df.empty or "display_symbol" not in df.columns:
        return {}
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    latest = df["date"].max()
    if pd.isna(latest):
        return {}
    sub = df[df["date"] == latest]
    return {str(r["display_symbol"]): int(r["news_count"]) for _, r in sub.iterrows() if pd.notna(r["display_symbol"])}


def _row_to_asset(row: pd.Series, news_counts: dict[str, int]) -> AssetOut | None:
    sym = str(row.get("display_symbol") or row.get("symbol") or "").strip()
    if not sym:
        return None

    name = _NAME.get(sym, sym)
    market = _MARKET.get(sym, "crypto")
    if market not in ("crypto", "forex", "metals"):
        market = "crypto"

    close = float(row.get("close", 0) or 0)
    ma7 = float(row.get("ma7", close) or close)
    ma30 = float(row.get("ma30", close) or close)
    ma20 = float(row.get("ma20", close) or close)
    ma50 = float(row.get("ma50", close) or close)
    rsi = float(row.get("rsi", 50) or 50)
    macd = float(row.get("macd", 0) or 0)
    macd_sig = float(row.get("macd_signal", 0) or 0)
    vol = float(row.get("volatility", 0) or 0)
    ret = float(row.get("returns", 0) or 0)
    corr = row.get("correlation")
    corr_f = float(corr) if corr is not None and pd.notna(corr) else None

    pred, conf, p_up, p_down = signal_from_features(
        close=close,
        ma7=ma7,
        ma30=ma30,
        rsi=rsi,
        returns=ret,
        volatility=vol,
    )

    feats = top_features_from_row(corr_f)
    top = [TopFeatureOut(name=n, weight=w) for n, w in ((f["name"], f["weight"]) for f in feats)]

    # Sentiment: use correlation sign as weak proxy until news aggregates are wired
    sentiment_score = max(-1.0, min(1.0, (corr_f or 0) * 1.5 + ret * 8.0))

    return AssetOut(
        symbol=sym,
        name=name,
        market=market,  # type: ignore[arg-type]
        price=close,
        changePct=ret * 100.0,
        volume=lakehouse.format_volume(row.get("volume")),
        rsi=rsi,
        macd=macd,
        macdSignal=macd_sig,
        volatility=vol,
        ma7=ma7,
        ma30=ma30,
        ma20=ma20,
        ma50=ma50,
        prediction=pred,
        confidence=conf,
        sentimentScore=sentiment_score,
        newsCount24h=int(news_counts.get(sym, 0)),
        lastReturn=ret,
        anomalies=lakehouse.anomalies_for_row(row),
        topFeatures=top,
        modelVersion="signal-engine-v1",
        probUp=p_up,
        probDown=p_down,
    )


def build_assets_list() -> list[AssetOut]:
    df = lakehouse.load_gold_market_enriched()
    if df.empty:
        return []
    latest = lakehouse.latest_per_display_symbol(df)
    news_counts = _news_counts_for_assets()
    assets: list[AssetOut] = []
    for _, row in latest.iterrows():
        a = _row_to_asset(row, news_counts)
        if a:
            assets.append(a)
    assets.sort(key=lambda x: x.symbol)
    return assets
