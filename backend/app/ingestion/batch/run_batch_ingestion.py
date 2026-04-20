import pandas as pd

from app.config.logging_config import get_logger

from app.ingestion.batch.coingecko_ingestor import CoinGeckoIngestor
from app.ingestion.batch.frankfurter_ingestor import FrankfurterIngestor
from app.ingestion.batch.yfinance_ingestion import YFinanceIngestor
from app.ingestion.batch.finnhub_news_ingestor import FinnhubNewsIngestor

from app.etl.bronze.write_bronze import write_bronze_table


logger = get_logger(__name__)


def run_crypto():
    logger.info("Starting crypto ingestion (daily snapshot, append)")

    ingestor = CoinGeckoIngestor()
    df = ingestor.fetch(historical=False)
    if df is None or df.empty:
        logger.warning("Crypto fetch returned no rows — skipping Bronze write")
        return

    write_bronze_table(
        df=df,
        dataset_name="crypto_prices",
        mode="append",
    )

    logger.info("Crypto ingestion finished")


def run_forex():
    logger.info("Starting forex ingestion (latest ECB date, append)")

    ingestor = FrankfurterIngestor()
    df = ingestor.fetch(historical=False)
    if df is None or df.empty:
        logger.warning("Forex fetch returned no rows — skipping Bronze write")
        return

    write_bronze_table(
        df=df,
        dataset_name="forex_rates",
        mode="append",
    )

    logger.info("Forex ingestion finished")


def run_metals():
    logger.info("Starting metals ingestion (daily yfinance snapshot, append)")

    ingestor = YFinanceIngestor()
    df = ingestor.fetch()
    if df is None or df.empty:
        logger.warning("Metals fetch returned no rows — skipping Bronze write")
        return

    write_bronze_table(
        df=df,
        dataset_name="metals_prices",
        mode="append",
    )

    logger.info("Metals ingestion finished")


def run_news():
    logger.info("Starting news ingestion (~1 day lookback, append)")
    # ingest() skips Bronze when fetch() is empty (missing API key, 401, quota, etc.)
    FinnhubNewsIngestor(lookback_days=1).ingest(mode="append")
    logger.info("News ingestion finished")


def run_all():
    logger.info("Starting batch ingestion pipeline")

    run_crypto()
    run_forex()
    run_metals()
    run_news()

    logger.info("Batch ingestion pipeline completed")


if __name__ == "__main__":
    run_all()