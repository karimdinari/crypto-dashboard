"""
CoinGecko batch ingestor for crypto price data.

- **Default (`historical=False`)**: current prices for each asset, one logical row
  per calendar day (UTC midnight in `timestamp`) — for daily append to Bronze.
- **`historical=True`**: multi-day history via `market_chart` (backfill / one-offs).
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from typing import Optional


def _utc_calendar_midnight_iso() -> str:
    """UTC midnight for today's date (as-of day for daily snapshots)."""
    now = datetime.now(timezone.utc)
    return datetime(now.year, now.month, now.day, tzinfo=timezone.utc).isoformat()

import pandas as pd

from app.config.assets import CRYPTO_ASSETS
from app.config.settings import COINGECKO_BASE_URL
from app.ingestion.batch.base_ingestor import BaseIngestor
from app.etl.bronze.write_bronze import write_bronze_table  # ✅ ADDED


class CoinGeckoIngestor(BaseIngestor):
    """Ingestor for CoinGecko crypto prices with historical data support"""

    def __init__(
        self,
        days: int = 365,
        start_date: Optional[str] = None,
        symbols: Optional[list[str]] = None,
    ):
        """
        Initialize CoinGecko ingestor.
        
        Args:
            days: Number of days of historical data to fetch (default: 365)
            start_date: Optional start date (YYYY-MM-DD or ISO). When provided,
                        uses CoinGecko range endpoint from this date to
                        start_date + days.
            symbols: Optional subset of CoinGecko ids, e.g. ["bitcoin"].
        """
        super().__init__(source_name="coingecko")
        self.base_url = COINGECKO_BASE_URL
        if symbols:
            wanted = {s.lower() for s in symbols}
            self.assets = [asset for asset in CRYPTO_ASSETS if asset.get("symbol", "").lower() in wanted]
        else:
            self.assets = CRYPTO_ASSETS
        self.days = int(days)
        self.start_date = start_date

        if not self.assets:
            self.logger.warning("No matching CoinGecko assets after symbol filtering")

    @staticmethod
    def _parse_utc_datetime(raw_value: str) -> datetime:
        """Parse date input and normalize to UTC."""
        try:
            dt = datetime.fromisoformat(raw_value)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            return datetime.strptime(raw_value, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    def fetch_current(self) -> Optional[pd.DataFrame]:
        """
        Fetch current price data for all crypto assets.

        Returns:
            DataFrame with current crypto price data or None
        """
        all_records = []

        for asset in self.assets:
            symbol = asset["symbol"]
            vs_currency = asset["vs_currency"]

            self.logger.info(
                f"Fetching current CoinGecko data for {symbol}",
                extra={"symbol": symbol, "vs_currency": vs_currency}
            )

            url = f"{self.base_url}/simple/price"

            params = {
                "ids": symbol,
                "vs_currencies": vs_currency,
                "include_market_cap": "true",
                "include_24hr_vol": "true",
            }

            try:
                response = self.get_json(url, params=params)

                if response and symbol in response:
                    price_data = response[symbol]

                    record = {
                        "symbol": symbol,
                        "display_symbol": asset["display_symbol"],
                        "market_type": "crypto",
                        "source": self.source_name,
                        "timestamp": _utc_calendar_midnight_iso(),
                        "price": price_data.get("usd"),
                        "market_cap": price_data.get("usd_market_cap"),
                        "total_volume": price_data.get("usd_24h_vol"),
                        "ingestion_time": self.get_ingestion_time().isoformat(),
                    }

                    all_records.append(record)

                    self.logger.info(
                        f"Successfully fetched {symbol}",
                        extra={"symbol": symbol, "price": record["price"]}
                    )
                else:
                    self.logger.warning(
                        f"No data in response for {symbol}",
                        extra={"symbol": symbol}
                    )

            except Exception as e:
                self.logger.error(
                    f"Failed to fetch {symbol}",
                    extra={"symbol": symbol, "error": str(e)}
                )

        if not all_records:
            self.logger.error("No crypto data collected")
            return None

        df = pd.DataFrame(all_records)
        return df

    def fetch_historical(self) -> Optional[pd.DataFrame]:
        """
        Fetch historical price data for all crypto assets.

        Returns:
            DataFrame with historical crypto price data or None
        """
        all_records = []
        ingestion_time = self.get_ingestion_time().isoformat()
        use_range_mode = bool(self.start_date)

        if use_range_mode:
            start_dt = self._parse_utc_datetime(self.start_date)
            end_dt = start_dt + timedelta(days=self.days)

        for asset in self.assets:
            symbol = asset["symbol"]
            vs_currency = asset["vs_currency"]

            if use_range_mode:
                self.logger.info(
                    f"Fetching range historical data for {symbol}",
                    extra={
                        "symbol": symbol,
                        "start_date": start_dt.isoformat(),
                        "end_date": end_dt.isoformat(),
                        "days": self.days,
                    }
                )
                url = f"{self.base_url}/coins/{symbol}/market_chart/range"
                params = {
                    "vs_currency": vs_currency,
                    "from": str(int(start_dt.timestamp())),
                    "to": str(int(end_dt.timestamp())),
                }
            else:
                self.logger.info(
                    f"Fetching {self.days} days of historical data for {symbol}",
                    extra={"symbol": symbol, "days": self.days}
                )
                # CoinGecko historical endpoint
                url = f"{self.base_url}/coins/{symbol}/market_chart"
                params = {
                    "vs_currency": vs_currency,
                    "days": str(self.days),
                    "interval": "daily",
                }

            try:
                response = self.get_json(url, params=params)

                if response and "prices" in response:
                    prices = response["prices"]
                    market_caps = response.get("market_caps", [])
                    volumes = response.get("total_volumes", [])

                    for i, price_entry in enumerate(prices):
                        timestamp_ms = price_entry[0]
                        price = price_entry[1]
                        timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat()

                        record = {
                            "symbol": symbol,
                            "display_symbol": asset["display_symbol"],
                            "market_type": "crypto",
                            "timestamp": timestamp,
                            "source": self.source_name,
                            "price": price,
                            "market_cap": market_caps[i][1] if i < len(market_caps) else None,
                            "total_volume": volumes[i][1] if i < len(volumes) else None,
                            "ingestion_time": ingestion_time,
                        }

                        all_records.append(record)

                    self.logger.info(
                        f"Successfully fetched {len(prices)} historical records for {symbol}",
                        extra={"symbol": symbol, "records": len(prices)}
                    )
                else:
                    self.logger.warning(
                        f"No historical data in response for {symbol}",
                        extra={"symbol": symbol}
                    )

            except Exception as e:
                self.logger.error(
                    f"Failed to fetch historical data for {symbol}",
                    extra={"symbol": symbol, "error": str(e)}
                )

        if not all_records:
            self.logger.error("No historical crypto data collected")
            return None

        df = pd.DataFrame(all_records)
        df = df.drop_duplicates(subset=["symbol", "timestamp"], keep="last")
        df = df.sort_values(["symbol", "timestamp"]).reset_index(drop=True)
        self.logger.info(
            f"CoinGecko historical ingestion complete",
            extra={"total_records": len(df), "days": self.days, "start_date": self.start_date}
        )

        return df

    def fetch(self, historical: bool = False) -> Optional[pd.DataFrame]:
        """
        Fetch crypto data (current daily snapshot or historical).

        Args:
            historical: If True, multi-day history; if False, today's snapshot (append-friendly).

        Returns:
            DataFrame with crypto price data or None
        """
        if historical:
            return self.fetch_historical()
        return self.fetch_current()

    def ingest_and_write(self, historical: bool = False, mode: str = "append") -> bool:
        """
        Fetch crypto data and write to Bronze layer.
        
        Args:
            historical: If True, multi-day history; if False, daily snapshot
            mode: Write mode - 'append' (default) or 'overwrite'
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(
            f"Starting CoinGecko ingestion ({'historical' if historical else 'current'}) with Bronze write"
        )
        
        try:
            df = self.fetch(historical=historical)
            
            if df is None or df.empty:
                self.logger.warning("No data to write to Bronze")
                return False
            
            output_path = write_bronze_table(
                df=df,
                dataset_name="crypto_prices",
                mode=mode
            )
            
            self.logger.info(
                f"✅ Crypto data written to Bronze",
                extra={
                    "output_path": str(output_path),
                    "records": len(df),
                    "mode": mode,
                    "historical": historical
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                f"❌ Failed to ingest and write crypto data",
                extra={"error": str(e)}
            )
            return False


def ingest_coingecko(
    days: int = 365,
    historical: bool = True,
    write_to_bronze: bool = False,
    mode: str = "append",
    start_date: Optional[str] = None,
    symbols: Optional[list[str]] = None,
) -> Optional[pd.DataFrame]:
    """
    Convenience function to run CoinGecko ingestion.

    Args:
        days: Number of days of historical data (default: 365)
        historical: If True, fetch historical; if False, fetch current
        write_to_bronze: If True, write to Bronze layer
        mode: Write mode - 'append' or 'overwrite'
        start_date: Optional start date (YYYY-MM-DD or ISO) for range fetch
        symbols: Optional subset of CoinGecko ids, e.g. ["bitcoin"]

    Returns:
        DataFrame with crypto price data
    """
    ingestor = CoinGeckoIngestor(days=days, start_date=start_date, symbols=symbols)
    df = ingestor.fetch(historical=historical)

    if df is not None and not df.empty and write_to_bronze:
        write_bronze_table(df=df, dataset_name="crypto_prices", mode=mode)

    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoinGecko historical ingestion")
    parser.add_argument("--days", type=int, default=365, help="Number of days to fetch")
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Optional start date (YYYY-MM-DD or ISO). Uses range endpoint.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="append",
        choices=["overwrite", "append"],
        help="Bronze write mode",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default=None,
        help="Optional CoinGecko id to ingest (example: bitcoin)",
    )
    parser.add_argument(
        "--current",
        action="store_true",
        help="Fetch current snapshot instead of historical",
    )
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("CoinGecko Ingestion -> Bronze Layer")
    print("=" * 60 + "\n")

    selected_symbols = [args.symbol] if args.symbol else None
    ingest_coingecko(
        days=args.days,
        historical=not args.current,
        write_to_bronze=True,
        mode=args.mode,
        start_date=args.start_date,
        symbols=selected_symbols,
    )