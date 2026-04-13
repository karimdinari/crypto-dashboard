from pathlib import Path
import pandas as pd

from app.config.logging_config import get_logger
from app.etl.gold.schema_gold import GOLD_NEWS_AGGREGATES_COLUMNS

logger = get_logger(__name__)

SILVER_NEWS_PATH = "lakehouse/silver/news_data/data.parquet"
GOLD_NEWS_DIR = "lakehouse/gold/news_aggregates"
GOLD_NEWS_FILE = "lakehouse/gold/news_aggregates/data.parquet"


def build_gold_news():
    logger.info("Reading Silver news dataset")

    df = pd.read_parquet(SILVER_NEWS_PATH)

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df["date"] = df["timestamp"].dt.date

    logger.info("Aggregating news by symbol and date")

    agg_df = (
        df.groupby(["symbol", "display_symbol", "market_type", "date"], as_index=False)
        .size()
        .rename(columns={"size": "news_count"})
    )

    agg_df = agg_df[GOLD_NEWS_AGGREGATES_COLUMNS]

    output_dir = Path(GOLD_NEWS_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    agg_df.to_parquet(GOLD_NEWS_FILE, index=False)

    logger.info(f"Gold news aggregates written to {GOLD_NEWS_FILE}")

    return agg_df


if __name__ == "__main__":
    build_gold_news()