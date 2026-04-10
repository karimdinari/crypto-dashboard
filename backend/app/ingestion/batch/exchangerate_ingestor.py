"""
ExchangeRate batch ingestor for forex rates.
Fetches EUR/USD and GBP/USD historical exchange rates.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from app.config.assets import FOREX_ASSETS
from app.config.settings import EXCHANGERATE_BASE_URL
from app.ingestion.batch.base_ingestor import BaseIngestor


class ExchangeRateIngestor(BaseIngestor):
    """Ingestor for Frankfurter forex rates with historical data support"""

    def __init__(self, days: int = 30) -> None:
        """
        Initialize ExchangeRate ingestor.
        
        Args:
            days: Number of days of historical data to fetch (default: 30)
        """
        super().__init__(source_name="frankfurter")
        self.base_url = EXCHANGERATE_BASE_URL
        self.assets = FOREX_ASSETS
        self.days = days

    def fetch_current(self) -> Optional[pd.DataFrame]:
        """
        Fetch current exchange rates for all forex pairs.

        Returns:
            DataFrame with current forex rate data or None
        """
        all_records = []
        ingestion_time = self.get_ingestion_time().isoformat()

        for asset in self.assets:
            base = asset["base_currency"]
            quote = asset["quote_currency"]
            symbol = asset["symbol"]

            self.logger.info(
                f"Fetching current rate for {base}/{quote}",
                extra={"base": base, "quote": quote}
            )

            url = f"{self.base_url}/latest"

            params = {
                "from": base,
                "to": quote,
            }

            try:
                response = self.get_json(url, params=params)

                if response and "rates" in response and quote in response["rates"]:
                    rate = response["rates"][quote]
                    date = response.get("date")

                    record = {
                        "symbol": symbol,
                        "display_symbol": asset["display_symbol"],
                        "market_type": "forex",
                        "source": "frankfurter",
                        "base_currency": base,
                        "quote_currency": quote,
                        "exchange_rate": rate,
                        "timestamp": date or ingestion_time,
                        "ingestion_time": ingestion_time,
                    }

                    all_records.append(record)

                    self.logger.info(
                        f"Successfully fetched {base}/{quote}",
                        extra={"symbol": symbol, "rate": rate}
                    )
                else:
                    self.logger.warning(
                        f"No rate data in response for {base}/{quote}",
                        extra={"base": base, "quote": quote}
                    )

            except Exception as e:
                self.logger.error(
                    f"Failed to fetch {base}/{quote}",
                    extra={"base": base, "quote": quote, "error": str(e)}
                )

        if not all_records:
            return None

        return pd.DataFrame(all_records)

    def fetch_historical(self) -> Optional[pd.DataFrame]:
        """
        Fetch historical exchange rates for all forex pairs.

        Returns:
            DataFrame with historical forex rate data or None
        """
        all_records = []
        ingestion_time = self.get_ingestion_time().isoformat()

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.days)

        for asset in self.assets:
            base = asset["base_currency"]
            quote = asset["quote_currency"]
            symbol = asset["symbol"]

            self.logger.info(
                f"Fetching {self.days} days of historical data for {base}/{quote}",
                extra={"base": base, "quote": quote, "days": self.days}
            )

            # Frankfurter historical endpoint
            url = f"{self.base_url}/{start_date.strftime('%Y-%m-%d')}.."

            params = {
                "from": base,
                "to": quote,
            }

            try:
                response = self.get_json(url, params=params)

                if response and "rates" in response:
                    rates_by_date = response["rates"]

                    for date_str, rate_data in rates_by_date.items():
                        if quote in rate_data:
                            rate = rate_data[quote]

                            record = {
                                "symbol": symbol,
                                "display_symbol": asset["display_symbol"],
                                "market_type": "forex",
                                "source": "frankfurter",
                                "base_currency": base,
                                "quote_currency": quote,
                                "exchange_rate": rate,
                                "timestamp": date_str,
                                "ingestion_time": ingestion_time,
                            }

                            all_records.append(record)

                    self.logger.info(
                        f"Successfully fetched {len(rates_by_date)} historical records for {base}/{quote}",
                        extra={"symbol": symbol, "records": len(rates_by_date)}
                    )
                else:
                    self.logger.warning(
                        f"No historical data in response for {base}/{quote}",
                        extra={"base": base, "quote": quote}
                    )

            except Exception as e:
                self.logger.error(
                    f"Failed to fetch historical data for {base}/{quote}",
                    extra={"base": base, "quote": quote, "error": str(e)}
                )

        if not all_records:
            self.logger.error("No historical forex data collected")
            return None

        df = pd.DataFrame(all_records)
        self.logger.info(
            f"Frankfurter historical ingestion complete",
            extra={"total_records": len(df), "days": self.days}
        )

        return df

    def fetch(self, historical: bool = True) -> Optional[pd.DataFrame]:
        """
        Fetch forex data (current or historical).

        Args:
            historical: If True, fetch historical data; if False, fetch current only

        Returns:
            DataFrame with forex rate data or None
        """
        if historical:
            return self.fetch_historical()
        else:
            return self.fetch_current()


def ingest_exchangerate(days: int = 30, historical: bool = True) -> Optional[pd.DataFrame]:
    """
    Convenience function to run ExchangeRate ingestion.

    Args:
        days: Number of days of historical data (default: 30)
        historical: If True, fetch historical; if False, fetch current

    Returns:
        DataFrame with forex rate data
    """
    ingestor = ExchangeRateIngestor(days=days)
    return ingestor.fetch(historical=historical)


if __name__ == "__main__":
    # Test run - fetch 30 days of historical data
    print("\n" + "="*60)
    print("Fetching 30 days of historical forex data...")
    print("="*60 + "\n")
    
    df = ingest_exchangerate(days=30, historical=True)

    if df is not None:
        print(f"\n✅ Forex Historical Ingestion Successful")
        print(f"Total Records: {len(df)}")
        print(f"Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"\nFirst 5 records:")
        print(df.head().to_string())
        print(f"\nLast 5 records:")
        print(df.tail().to_string())
    else:
        print("\n❌ Forex Ingestion Failed")