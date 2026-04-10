"""
CoinGecko batch ingestor for crypto price data.
Fetches Bitcoin and Ethereum prices and market data.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from app.config.assets import CRYPTO_ASSETS
from app.config.settings import COINGECKO_BASE_URL
from app.ingestion.batch.base_ingestor import BaseIngestor


class CoinGeckoIngestor(BaseIngestor):
    """Ingestor for CoinGecko crypto prices"""

    def __init__(self) -> None:
        super().__init__(source_name="coingecko")
        self.base_url = COINGECKO_BASE_URL
        self.assets = CRYPTO_ASSETS

    def fetch(self) -> Optional[pd.DataFrame]:
        """
        Fetch current price data for all crypto assets.

        Returns:
            DataFrame with crypto price data or None
        """
        all_records = []

        for asset in self.assets:
            symbol = asset["symbol"]
            vs_currency = asset["vs_currency"]

            self.logger.info(
                f"Fetching CoinGecko data for {symbol}",
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
        self.logger.info(
            f"CoinGecko ingestion complete",
            extra={"total_records": len(df)}
        )

        return df


def ingest_coingecko() -> Optional[pd.DataFrame]:
    """
    Convenience function to run CoinGecko ingestion.

    Returns:
        DataFrame with crypto price data
    """
    ingestor = CoinGeckoIngestor()
    return ingestor.fetch()


if __name__ == "__main__":
    # Test run
    df = ingest_coingecko()

    if df is not None:
        print("\n✅ CoinGecko Ingestion Successful")
        print(f"Records: {len(df)}")
        print("\nSample data:")
        print(df.to_string())
    else:
        print("\n❌ CoinGecko Ingestion Failed")