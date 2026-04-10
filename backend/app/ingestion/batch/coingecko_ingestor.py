"""
CoinGecko batch ingestor for crypto price data.
Fetches Bitcoin and Ethereum historical prices and market data.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from app.config.assets import CRYPTO_ASSETS
from app.config.settings import COINGECKO_BASE_URL
from app.ingestion.batch.base_ingestor import BaseIngestor


class CoinGeckoIngestor(BaseIngestor):
    """Ingestor for CoinGecko crypto prices with historical data support"""

    def __init__(self, days: int = 30) -> None:
        """
        Initialize CoinGecko ingestor.
        
        Args:
            days: Number of days of historical data to fetch (default: 30)
                  Max for free tier: 365 days
        """
        super().__init__(source_name="coingecko")
        self.base_url = COINGECKO_BASE_URL
        self.assets = CRYPTO_ASSETS
        self.days = days

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
                        "timestamp": self.get_ingestion_time().isoformat(),
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

        for asset in self.assets:
            symbol = asset["symbol"]
            vs_currency = asset["vs_currency"]

            self.logger.info(
                f"Fetching {self.days} days of historical data for {symbol}",
                extra={"symbol": symbol, "days": self.days}
            )

            # CoinGecko historical endpoint
            url = f"{self.base_url}/coins/{symbol}/market_chart"

            params = {
                "vs_currency": vs_currency,
                "days": str(self.days),
                "interval": "daily",  # daily data points
            }

            try:
                response = self.get_json(url, params=params)

                if response and "prices" in response:
                    prices = response["prices"]
                    market_caps = response.get("market_caps", [])
                    volumes = response.get("total_volumes", [])

                    # Each item is [timestamp_ms, value]
                    for i, price_entry in enumerate(prices):
                        timestamp_ms = price_entry[0]
                        price = price_entry[1]
                        
                        # Convert timestamp to datetime
                        dt = datetime.fromtimestamp(timestamp_ms / 1000)

                        record = {
                            "symbol": symbol,
                            "display_symbol": asset["display_symbol"],
                            "market_type": "crypto",
                            "source": self.source_name,
                            "price": price,
                            "market_cap": market_caps[i][1] if i < len(market_caps) else None,
                            "total_volume": volumes[i][1] if i < len(volumes) else None,
                            "timestamp": dt.isoformat(),
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
        self.logger.info(
            f"CoinGecko historical ingestion complete",
            extra={"total_records": len(df), "days": self.days}
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


def ingest_coingecko(days: int = 30, historical: bool = True) -> Optional[pd.DataFrame]:
    """
    Convenience function to run CoinGecko ingestion.

    Args:
        days: Number of days of historical data (default: 30)
        historical: If True, fetch historical; if False, fetch current

    Returns:
        DataFrame with crypto price data
    """
    ingestor = CoinGeckoIngestor(days=days)
    return ingestor.fetch(historical=historical)


if __name__ == "__main__":
    # Test run - fetch 30 days of historical data
    print("\n" + "="*60)
    print("Fetching 30 days of historical crypto data...")
    print("="*60 + "\n")
    
    df = ingest_coingecko(days=30, historical=True)

    if df is not None:
        print(f"\n✅ CoinGecko Historical Ingestion Successful")
        print(f"Total Records: {len(df)}")
        print(f"Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"\nFirst 5 records:")
        print(df.head().to_string())
        print(f"\nLast 5 records:")
        print(df.tail().to_string())
    else:
        print("\n❌ CoinGecko Ingestion Failed")