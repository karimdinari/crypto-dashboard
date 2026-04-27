import pandas as pd
from pathlib import Path

from app.config.logging_config import get_logger
from app.config.settings import BRONZE_PATH, SILVER_PATH
from app.etl.silver.schema_silver import SILVER_NEWS_COLUMNS
from app.features.sentiment_analyzer import SentimentAnalyzer

logger = get_logger(__name__)

BRONZE_NEWS_PATH = Path(BRONZE_PATH) / "news" / "data.parquet"

SILVER_NEWS_DIR = Path(SILVER_PATH) / "news_data"
SILVER_NEWS_FILE = SILVER_NEWS_DIR / "data.parquet"


def clean_news():
    logger.info("Reading Bronze news dataset")

    if not BRONZE_NEWS_PATH.exists():
        logger.warning(f"Bronze news file not found: {BRONZE_NEWS_PATH}")
        return pd.DataFrame(columns=SILVER_NEWS_COLUMNS)

    df = pd.read_parquet(BRONZE_NEWS_PATH)

    if df.empty:
        logger.warning("Bronze news dataset is empty")
        return pd.DataFrame(columns=SILVER_NEWS_COLUMNS)

    logger.info("Cleaning news dataset")

    # normalize timestamp
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
        utc=True
    )

    # clean text
    text_cols = ["title", "summary", "url", "source_name", "symbol", "display_symbol", "market_type", "source"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # drop invalid rows
    df = df.dropna(subset=["news_id", "timestamp", "symbol"])

    # remove duplicates
    df = df.drop_duplicates(subset=["news_id"])

    # sort
    df = df.sort_values("timestamp").reset_index(drop=True)

    logger.info("Running FinBERT sentiment analysis")
    analyzer = SentimentAnalyzer()
    df = analyzer.score_dataframe(df, text_col="title", summary_col="summary")

    # ensure all schema columns exist
    for col in SILVER_NEWS_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # enforce schema order
    df = df[SILVER_NEWS_COLUMNS]

    SILVER_NEWS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(SILVER_NEWS_FILE, index=False)

    logger.info(f"Silver news dataset written to {SILVER_NEWS_FILE}")

    return df


if __name__ == "__main__":
    clean_news()