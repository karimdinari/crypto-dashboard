"""
CoinGecko batch ingestor for crypto price data.
Fetches Bitcoin and Ethereum historical prices and market data.
Automatically writes to Bronze layer.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from typing import Optional

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

    def fetch(self, historical: bool = True) -> Optional[pd.DataFrame]:
        """
        Fetch crypto data (current or historical).

        Args:
            historical: If True, fetch historical data; if False, fetch current only

        Returns:
            DataFrame with crypto price data or None
        """
        if historical:
            return self.fetch_historical()
        else:
            return self.fetch_current()

    def ingest_and_write(self, historical: bool = True, mode: str = "overwrite") -> bool:
        """
        Fetch crypto data and write to Bronze layer.
        
        Args:
            historical: If True, fetch historical; if False, fetch current
            mode: Write mode - 'append' or 'overwrite'
            
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
    mode: str = "overwrite",
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
    
    if write_to_bronze:
        success = ingestor.ingest_and_write(historical=historical, mode=mode)
        if success:
            return ingestor.fetch(historical=historical)
        return None
    else:
        return ingestor.fetch(historical=historical)


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
        default="overwrite",
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
    ingestor = CoinGeckoIngestor(days=args.days, start_date=args.start_date, symbols=selected_symbols)
    success = ingestor.ingest_and_write(historical=not args.current, mode=args.mode)

    if success:
        print("\nCoinGecko ingestion successful")
        print("Data written to: lakehouse/bronze/crypto_prices/data.parquet")
    else:
        print("\nCoinGecko ingestion failed")