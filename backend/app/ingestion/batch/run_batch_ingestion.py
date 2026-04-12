import pandas as pd

from app.config.logging_config import get_logger

from app.ingestion.batch.coingecko_ingestor import CoinGeckoIngestor
from app.ingestion.batch.exchangerate_ingestor import ExchangeRateIngestor
from app.ingestion.batch.metals_csv_ingestor import MetalsCsvIngestor
from app.ingestion.batch.finnhub_news_ingestor import FinnhubNewsIngestor

from app.etl.bronze.write_bronze import write_bronze_table


logger = get_logger(__name__)


def run_crypto():
    logger.info("Starting crypto ingestion")

    ingestor = CoinGeckoIngestor()
    df = ingestor.fetch()

    write_bronze_table(
        df=df,
        dataset_name="crypto_prices",
        mode="overwrite"
    )

    logger.info("Crypto ingestion finished")


def run_forex():
    logger.info("Starting forex ingestion")

    ingestor = ExchangeRateIngestor()
    df = ingestor.fetch()

    write_bronze_table(
        df=df,
        dataset_name="forex_rates",
        mode="overwrite"
    )

    logger.info("Forex ingestion finished")


def run_metals():
    logger.info("Starting metals ingestion")

    ingestor = MetalsCsvIngestor()
    df = ingestor.fetch()

    write_bronze_table(
        df=df,
        dataset_name="metals_prices",
        mode="overwrite"
    )

    logger.info("Metals ingestion finished")


def run_news():
    logger.info("Starting news ingestion")
    # ingest() skips Bronze when fetch() is empty (missing API key, 401, quota, etc.)
    FinnhubNewsIngestor().ingest(mode="overwrite")
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