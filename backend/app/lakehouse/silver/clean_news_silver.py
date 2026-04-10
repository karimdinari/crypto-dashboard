import pandas as pd
from pathlib import Path

from app.config.logging_config import get_logger
from app.lakehouse.silver.schema_silver import SILVER_NEWS_COLUMNS

logger = get_logger(__name__)

BRONZE_NEWS_PATH = "lakehouse/bronze/news/data.parquet"

SILVER_NEWS_DIR = "lakehouse/silver/news_data"
SILVER_NEWS_FILE = "lakehouse/silver/news_data/data.parquet"


def clean_news():
    logger.info("Reading Bronze news dataset")

    df = pd.read_parquet(BRONZE_NEWS_PATH)

    logger.info("Cleaning news dataset")

    # normalize timestamp
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
        utc=True
    )

    # clean text
    text_cols = ["title", "summary", "url", "source_name"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # drop invalid rows
    df = df.dropna(subset=["news_id", "timestamp", "symbol"])

    # remove duplicates
    df = df.drop_duplicates(subset=["news_id"])

    # sort
    df = df.sort_values("timestamp")

    # enforce schema
    existing = [c for c in SILVER_NEWS_COLUMNS if c in df.columns]
    df = df[existing]

    # reset index
    df = df.reset_index(drop=True)

    output_dir = Path(SILVER_NEWS_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    df.to_parquet(SILVER_NEWS_FILE, index=False)

    logger.info(f"Silver news dataset written to {SILVER_NEWS_FILE}")

    return df


if __name__ == "__main__":
    clean_news()