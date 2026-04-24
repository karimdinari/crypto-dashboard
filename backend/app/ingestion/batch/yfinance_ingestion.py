from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import yfinance as yf

from app.config.assets import METALS_ASSETS
from app.ingestion.batch.base_ingestor import BaseIngestor
from app.etl.bronze.write_bronze import write_bronze_table


def _to_utc_midnight_iso(ts: pd.Timestamp) -> str:
    """Convert bar date to UTC midnight ISO string."""
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return datetime(ts.year, ts.month, ts.day, tzinfo=timezone.utc).isoformat()


def _pick_numeric(latest: pd.Series, field: str) -> float | None:
    """
    Read a scalar OHLCV value from a yfinance row.

    yfinance can return either:
    - flat columns: Open, High, Low, Close, Volume
    - multi-index columns where latest[field] is a Series (e.g. per ticker)
    """
    if field not in latest.index:
        return None
    value = latest[field]
    if isinstance(value, pd.Series):
        value = value.dropna()
        if value.empty:
            return None
        value = value.iloc[0]
    if pd.isna(value):
        return None
    return float(value)


class YFinanceIngestor(BaseIngestor):
    """
    Daily metals ingestor using Yahoo Finance.

    Pulls latest daily OHLCV bar for each metals ticker in METALS_ASSETS and
    writes append-friendly Bronze rows.
    """

    def __init__(self) -> None:
        super().__init__(source_name="yfinance")
        self.assets = METALS_ASSETS

    def fetch(self) -> pd.DataFrame:
        """Fetch one latest daily OHLCV row per metals symbol."""
        rows: list[dict] = []
        ingestion_time = self.get_ingestion_time().isoformat()

        for asset in self.assets:
            symbol = asset["symbol"]
            display_symbol = asset["display_symbol"]

            try:
                self.logger.info("Fetching latest daily metals bar", extra={"symbol": symbol})
                # 5d window handles weekends/holidays while still returning latest trading day.
                df = yf.download(
                    tickers=symbol,
                    period="5d",
                    interval="1d",
                    progress=False,
                    auto_adjust=False,
                    threads=False,
                )
            except Exception as exc:
                self.logger.error(
                    "YFinance request failed",
                    extra={"symbol": symbol, "error": str(exc)},
                )
                continue

            if df is None or df.empty:
                self.logger.warning("No yfinance bars returned", extra={"symbol": symbol})
                continue

            latest = df.iloc[-1]
            bar_ts = pd.Timestamp(df.index[-1])

            row = {
                "symbol": symbol,
                "display_symbol": display_symbol,
                "market_type": asset["market_type"],
                "source": asset.get("source", self.source_name),
                "timestamp": _to_utc_midnight_iso(bar_ts),
                "open": _pick_numeric(latest, "Open"),
                "high": _pick_numeric(latest, "High"),
                "low": _pick_numeric(latest, "Low"),
                "close": _pick_numeric(latest, "Close"),
                "volume": _pick_numeric(latest, "Volume"),
                "ingestion_time": ingestion_time,
            }

            if any(row[col] is None for col in ["open", "high", "low", "close"]):
                self.logger.warning(
                    "Dropping metals row with null OHLC",
                    extra={"symbol": symbol, "timestamp": row["timestamp"]},
                )
                continue

            rows.append(row)

        if not rows:
            return pd.DataFrame()

        out = pd.DataFrame(rows)
        self.logger.info("YFinance metals ingestion complete", extra={"rows": len(out)})
        return out

    def ingest(self, mode: str = "append") -> None:
        """Fetch and write metals rows to Bronze."""
        df = self.fetch()
        if df.empty:
            self.logger.warning("No metals rows to write")
            return
        write_bronze_table(df, dataset_name="metals_prices", mode=mode)  # type: ignore[arg-type]
        self.logger.info("Metals written to Bronze", extra={"rows": len(df), "mode": mode})


if __name__ == "__main__":
    YFinanceIngestor().ingest(mode="append")
