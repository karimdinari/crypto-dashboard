import argparse
from datetime import date
import pandas as pd

from app.config.logging_config import get_logger

from app.ingestion.batch.coingecko_ingestor import CoinGeckoIngestor
from app.ingestion.batch.crypto_csv_ingestor import CryptoCsvIngestor
from app.ingestion.batch.frankfurter_ingestor import FrankfurterIngestor
from app.ingestion.batch.yfinance_ingestion import YFinanceIngestor
from app.ingestion.batch.finnhub_news_ingestor import FinnhubNewsIngestor

from app.etl.bronze.write_bronze import write_bronze_table


logger = get_logger(__name__)


def run_crypto(
    days: int = 365,
    start_date: str | None = None,
    mode: str = "overwrite",
    historical: bool = True,
    symbol: str | None = None,
):
    logger.info("Starting crypto ingestion")

    symbols = [symbol] if symbol else None
    frames: list[pd.DataFrame] = []

    # 1) Static bootstrap history from local Kaggle CSV files.
    try:
        csv_ingestor = CryptoCsvIngestor(symbols=symbols)
        csv_df = csv_ingestor.fetch()
        if csv_df is not None and not csv_df.empty:
            frames.append(csv_df)
            logger.info("Loaded static crypto CSV seed data", extra={"rows": len(csv_df)})
    except Exception as exc:
        logger.warning("Static crypto CSV ingestion failed", extra={"error": str(exc)})

    # 2) Fresh pull from CoinGecko.
    try:
        api_ingestor = CoinGeckoIngestor(days=days, start_date=start_date, symbols=symbols)
        api_df = api_ingestor.fetch(historical=historical)
        if api_df is not None and not api_df.empty:
            frames.append(api_df)
            logger.info("Loaded fresh CoinGecko crypto data", extra={"rows": len(api_df)})
    except Exception as exc:
        logger.warning("Fresh CoinGecko ingestion failed", extra={"error": str(exc)})

    if not frames:
        logger.warning("No crypto data fetched from CSV or CoinGecko; skipping Bronze write")
        return

    df = pd.concat(frames, ignore_index=True)
    # Keep newest observation for each symbol/timestamp (CoinGecko rows appended after CSV).
    if "timestamp" in df.columns:
        df = df.drop_duplicates(subset=["symbol", "timestamp"], keep="last")
        df = df.sort_values(["symbol", "timestamp"]).reset_index(drop=True)

    write_bronze_table(
        df=df,
        dataset_name="crypto_prices",
        mode=mode,
    )

    logger.info(
        "Crypto ingestion finished",
        extra={
            "records": len(df),
            "mode": mode,
            "historical": historical,
            "start_date": start_date,
            "symbol": symbol,
        },
    )


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


def run_all_with_crypto_options(
    days: int,
    start_date: str | None,
    crypto_mode: str,
    current: bool,
    symbol: str | None,
):
    """Run full pipeline while customizing the crypto ingestion step."""
    logger.info("Starting batch ingestion pipeline with custom crypto options")

    run_crypto(
        days=days,
        start_date=start_date,
        mode=crypto_mode,
        historical=not current,
        symbol=symbol,
    )
    run_forex()
    run_metals()
    run_news()

    logger.info("Batch ingestion pipeline completed")


def run_crypto_backfill_years(start_year: int, end_year: int, symbol: str | None = None):
    """Backfill crypto year by year with overwrite for first year, then append."""
    if start_year > end_year:
        raise ValueError("start_year must be <= end_year")

    logger.info(
        "Starting yearly crypto backfill",
        extra={"start_year": start_year, "end_year": end_year, "symbol": symbol},
    )

    current_year = date.today().year
    for idx, year in enumerate(range(start_year, end_year + 1)):
        start_date = f"{year}-01-01"
        mode = "overwrite" if idx == 0 else "append"

        # For the current year, fetch only up to today.
        if year == current_year:
            jan1 = date(year, 1, 1)
            days = max(1, (date.today() - jan1).days + 1)
        else:
            days = 365

        logger.info(
            "Running yearly crypto chunk",
            extra={"year": year, "start_date": start_date, "days": days, "mode": mode},
        )
        run_crypto(
            days=days,
            start_date=start_date,
            mode=mode,
            historical=True,
            symbol=symbol,
        )

    logger.info("Yearly crypto backfill completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run batch ingestion pipeline")
    parser.add_argument(
        "--crypto-days",
        type=int,
        default=365,
        help="Number of crypto history days to fetch",
    )
    parser.add_argument(
        "--crypto-start-date",
        type=str,
        default=None,
        help="Crypto start date (YYYY-MM-DD or ISO) for range mode",
    )
    parser.add_argument(
        "--crypto-mode",
        type=str,
        default="overwrite",
        choices=["overwrite", "append"],
        help="Bronze write mode for crypto dataset",
    )
    parser.add_argument(
        "--crypto-current",
        action="store_true",
        help="Fetch current crypto snapshot instead of historical",
    )
    parser.add_argument(
        "--crypto-symbol",
        type=str,
        default=None,
        help="Optional single CoinGecko symbol (default: all configured assets)",
    )
    parser.add_argument(
        "--only-crypto",
        action="store_true",
        help="Run only the crypto ingestion step",
    )
    parser.add_argument(
        "--backfill-start-year",
        type=int,
        default=None,
        help="If provided, run yearly crypto backfill from this year",
    )
    parser.add_argument(
        "--backfill-end-year",
        type=int,
        default=None,
        help="Optional end year for yearly crypto backfill (defaults to current year)",
    )
    # Short aliases for easier direct usage.
    parser.add_argument("--start-date", type=str, default=None, help="Alias of --crypto-start-date")
    parser.add_argument("--days", type=int, default=None, help="Alias of --crypto-days")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["overwrite", "append"],
        default=None,
        help="Alias of --crypto-mode",
    )
    args = parser.parse_args()

    resolved_start_date = args.start_date if args.start_date is not None else args.crypto_start_date
    resolved_days = args.days if args.days is not None else args.crypto_days
    resolved_mode = args.mode if args.mode is not None else args.crypto_mode

    if args.backfill_start_year is not None:
        end_year = args.backfill_end_year if args.backfill_end_year is not None else date.today().year
        run_crypto_backfill_years(
            start_year=args.backfill_start_year,
            end_year=end_year,
            symbol=args.crypto_symbol,
        )
    elif args.only_crypto:
        run_crypto(
            days=resolved_days,
            start_date=resolved_start_date,
            mode=resolved_mode,
            historical=not args.crypto_current,
            symbol=args.crypto_symbol,
        )
    else:
        run_all_with_crypto_options(
            days=resolved_days,
            start_date=resolved_start_date,
            crypto_mode=resolved_mode,
            current=args.crypto_current,
            symbol=args.crypto_symbol,
        )