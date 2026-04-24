"""
News Sentiment Silver Layer
============================
Reads Silver news_data/data.parquet, runs sentiment analysis on every
article, and writes the enriched table to Silver news_sentiment/data.parquet.

This is a *separate* Silver table — it does NOT overwrite the clean news
table produced by clean_news_silver.py. Downstream Gold aggregations
read from this enriched table.

Run from backend/:
    python -m app.etl.silver.news_sentiment_silver

Or import and call directly:
    from app.etl.silver.news_sentiment_silver import run_news_sentiment_silver
    df = run_news_sentiment_silver()
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from app.config.logging_config import get_logger
from app.config.settings import SILVER_PATH
from app.features.sentiment_analyzer import SentimentAnalyzer

logger = get_logger("news_sentiment_silver")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SILVER_NEWS_FILE = Path(SILVER_PATH) / "news_data" / "data.parquet"
SILVER_SENTIMENT_DIR = Path(SILVER_PATH) / "news_sentiment"
SILVER_SENTIMENT_FILE = SILVER_SENTIMENT_DIR / "data.parquet"

# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

SENTIMENT_COLUMNS = [
    # ── Inherited from Silver news ──────────────────────────────────────
    "news_id",
    "timestamp",
    "symbol",
    "display_symbol",
    "market_type",
    "title",
    "summary",
    "url",
    "source_name",
    "source",
    "ingestion_time",
    # ── Sentiment ───────────────────────────────────────────────────────
    "sentiment_label",       # "positive" | "neutral" | "negative"
    "sentiment_score",       # confidence of the label   (0–1)
    "sentiment_compound",    # signed compound score     (-1 to +1)
    "sentiment_model",       # "finbert" | "vader"
    "sentiment_time",        # UTC ISO timestamp of when scoring ran
]


# ---------------------------------------------------------------------------
# Incremental helpers
# ---------------------------------------------------------------------------

def _already_scored_ids(output_file: Path) -> set[str]:
    """
    Return the set of news_ids that were already scored in a previous run.
    Used to avoid re-scoring unchanged articles (incremental mode).
    """
    if not output_file.exists():
        return set()
    try:
        existing = pd.read_parquet(output_file, columns=["news_id"])
        return set(existing["news_id"].dropna().astype(str))
    except Exception as exc:
        logger.warning(f"Could not read existing sentiment file: {exc}. Will re-score all.")
        return set()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_news_sentiment_silver(
    *,
    incremental: bool = True,
    write_silver: bool = True,
    batch_size: int = 32,
) -> pd.DataFrame:
    """
    Score Silver news articles with FinBERT and write the enriched table.

    Args:
        incremental:  If True, skip articles whose news_id is already
                      present in the output file (avoids re-scoring).
                      Set to False to re-score everything from scratch.
        write_silver: If False, return the DataFrame without writing to disk.
        batch_size:   Mini-batch size for FinBERT inference.
                      32 is safe on CPU; raise to 64+ on GPU.

    Returns:
        Enriched DataFrame with sentiment columns.
    """
    logger.info("Starting news sentiment Silver enrichment")

    if not SILVER_NEWS_FILE.exists():
        raise FileNotFoundError(
            f"Silver news file not found: {SILVER_NEWS_FILE}\n"
            "Run clean_news_silver first: python -m app.etl.silver.clean_news_silver"
        )

    # ── Load source news ─────────────────────────────────────────────────
    news_df = pd.read_parquet(SILVER_NEWS_FILE)
    logger.info("Silver news loaded", extra={"rows": len(news_df)})

    if news_df.empty:
        logger.warning("Silver news DataFrame is empty — nothing to score.")
        return pd.DataFrame(columns=SENTIMENT_COLUMNS)

    # ── Incremental: skip already-scored articles ────────────────────────
    scored_ids: set[str] = set()
    existing_df: pd.DataFrame = pd.DataFrame()

    if incremental:
        scored_ids = _already_scored_ids(SILVER_SENTIMENT_FILE)
        if scored_ids:
            logger.info(
                "Incremental mode: skipping already-scored articles",
                extra={"already_scored": len(scored_ids)},
            )
            existing_df = pd.read_parquet(SILVER_SENTIMENT_FILE)
            news_df = news_df[~news_df["news_id"].astype(str).isin(scored_ids)].copy()

    if news_df.empty:
        logger.info("No new articles to score — output is up to date.")
        return existing_df if not existing_df.empty else pd.DataFrame(columns=SENTIMENT_COLUMNS)

    logger.info("Articles to score", extra={"count": len(news_df)})

    # ── Sentiment scoring ────────────────────────────────────────────────
    analyzer = SentimentAnalyzer(batch_size=batch_size)

    scored_df = analyzer.score_dataframe(
        news_df,
        text_col="title",
        summary_col="summary",
    )

    sentiment_time = datetime.now(timezone.utc).isoformat()
    scored_df["sentiment_time"] = sentiment_time

    # ── Merge with existing scored rows (incremental) ────────────────────
    if not existing_df.empty:
        scored_df = pd.concat([existing_df, scored_df], ignore_index=True)
        scored_df = scored_df.drop_duplicates(subset=["news_id"], keep="last")

    # ── Enforce schema ───────────────────────────────────────────────────
    scored_df["timestamp"] = pd.to_datetime(scored_df["timestamp"], utc=True, errors="coerce")
    scored_df = scored_df.sort_values("timestamp").reset_index(drop=True)

    # keep only known columns (in order), add missing ones as None
    for col in SENTIMENT_COLUMNS:
        if col not in scored_df.columns:
            scored_df[col] = None
    scored_df = scored_df[SENTIMENT_COLUMNS]

    logger.info(
        "Sentiment scoring summary",
        extra={
            "total_rows": len(scored_df),
            "positive": (scored_df["sentiment_label"] == "positive").sum(),
            "neutral": (scored_df["sentiment_label"] == "neutral").sum(),
            "negative": (scored_df["sentiment_label"] == "negative").sum(),
            "model": analyzer.model_name,
        },
    )

    # ── Write ────────────────────────────────────────────────────────────
    if write_silver:
        SILVER_SENTIMENT_DIR.mkdir(parents=True, exist_ok=True)
        scored_df.to_parquet(SILVER_SENTIMENT_FILE, index=False)
        logger.info(
            "Silver news sentiment written",
            extra={"rows": len(scored_df), "path": str(SILVER_SENTIMENT_FILE)},
        )

    return scored_df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    df = run_news_sentiment_silver(incremental=True)

    print("\n✅ Silver news_sentiment written")
    print(f"   Rows    : {len(df)}")
    print(f"   Path    : {SILVER_SENTIMENT_FILE}\n")

    if not df.empty:
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 200)

        print("Label distribution:")
        print(df["sentiment_label"].value_counts().to_string())

        print("\nSample rows:")
        sample_cols = ["display_symbol", "timestamp", "title", "sentiment_label", "sentiment_compound"]
        print(df[sample_cols].head(10).to_string(index=False))