"""
ExchangeRate batch ingestor for forex rates.
Fetches EUR/USD and GBP/USD exchange rates.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from app.config.assets import FOREX_ASSETS
from app.config.settings import EXCHANGERATE_BASE_URL
from app.ingestion.batch.base_ingestor import BaseIngestor


class ExchangeRateIngestor(BaseIngestor):
    """Ingestor for ExchangeRate.host forex rates"""

    def __init__(self) -> None:
        super().__init__(source_name="exchangerate")
        self.base_url = EXCHANGERATE_BASE_URL
        self.assets = FOREX_ASSETS

    def fetch(self) -> Optional[pd.DataFrame]:
        """
        Fetch current exchange rates for all forex pairs.

        Returns:
            DataFrame with forex rate data or None
        """
        all_records = []

        for asset in self.assets:
            base = asset["base_currency"]
            quote = asset["quote_currency"]
            symbol = asset["symbol"]

            self.logger.info(
                f"Fetching ExchangeRate data for {base}/{quote}",
                extra={"base": base, "quote": quote}
            )

            url = f"{self.base_url}/latest"

            params = {
                "base": base,
                "symbols": quote,
            }

            try:
                response = self.get_json(url, params=params)

                # ✅ DEBUG: Print the full response
                self.logger.info(
                    f"Full API response for {base}/{quote}",
                    extra={"response": response}
                )

                # Check if the response has the expected structure
                if response and "rates" in response and quote in response["rates"]:
                    rate = response["rates"][quote]

                    record = {
                        "symbol": symbol,
                        "display_symbol": asset["display_symbol"],
                        "market_type": "forex",
                        "source": self.source_name,
                        "base_currency": base,
                        "quote_currency": quote,
                        "exchange_rate": rate,
                        "ingestion_time": self.get_ingestion_time().isoformat(),
                    }

                    all_records.append(record)

                    self.logger.info(
                        f"Successfully fetched {base}/{quote}",
                        extra={"symbol": symbol, "rate": rate}
                    )
                else:
                    # ✅ Show what keys exist in response
                    available_keys = list(response.keys()) if response else []
                    self.logger.warning(
                        f"No rate data in response for {base}/{quote}",
                        extra={
                            "base": base,
                            "quote": quote,
                            "available_keys": available_keys,
                            "has_rates": "rates" in response if response else False
                        }
                    )

            except Exception as e:
                self.logger.error(
                    f"Failed to fetch {base}/{quote}",
                    extra={"base": base, "quote": quote, "error": str(e)}
                )

        if not all_records:
            self.logger.error("No forex data collected")
            return None

        df = pd.DataFrame(all_records)
        self.logger.info(
            f"ExchangeRate ingestion complete",
            extra={"total_records": len(df)}
        )

        return df


def ingest_exchangerate() -> Optional[pd.DataFrame]:
    """
    Convenience function to run ExchangeRate ingestion.

    Returns:
        DataFrame with forex rate data
    """
    ingestor = ExchangeRateIngestor()
    return ingestor.fetch()


if __name__ == "__main__":
    # Test run
    df = ingest_exchangerate()

    if df is not None:
        print("\n✅ ExchangeRate Ingestion Successful")
        print(f"Records: {len(df)}")
        print("\nSample data:")
        print(df.to_string())
    else:
        print("\n❌ ExchangeRate Ingestion Failed")