"""
Gold News Builder v2 — with VADER Sentiment
=============================================
Reads Silver news (title + summary text), computes:
  - VADER sentiment per article
  - Daily aggregates per (symbol, date):
      news_count, sentiment_score (mean compound),
      sentiment_positive, sentiment_negative, sentiment_neutral

Falls back gracefully when vaderSentiment is not installed
(uses neutral 0.0 scores).

Run:
    pip install vaderSentiment
    python -m app.etl.gold.build_gold_news
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np

from app.config.logging_config import get_logger
from app.etl.gold.schema_gold import GOLD_NEWS_AGGREGATES_COLUMNS

logger = get_logger(__name__)

SILVER_NEWS_PATH = "lakehouse/silver/news_data/data.parquet"
GOLD_NEWS_DIR    = "lakehouse/gold/news_aggregates"
GOLD_NEWS_FILE   = "lakehouse/gold/news_aggregates/data.parquet"


# ---------------------------------------------------------------------------
# VADER helper
# ---------------------------------------------------------------------------

def _get_analyzer():
    """Return VADER SentimentIntensityAnalyzer, or None if not installed."""
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        return SentimentIntensityAnalyzer()
    except ImportError:
        try:
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            return SentimentIntensityAnalyzer()
        except Exception:
            logger.warning(
                "vaderSentiment not available — install with: pip install vaderSentiment"
            )
            return None


def _score_text(analyzer, text: str) -> dict:
    """Return VADER scores dict for a text string."""
    if not text or not isinstance(text, str) or text.strip() in ("", "nan"):
        return {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0}
    try:
        return analyzer.polarity_scores(text)
    except Exception:
        return {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0}


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_gold_news() -> pd.DataFrame:
    logger.info("Reading Silver news dataset")
    df = pd.read_parquet(SILVER_NEWS_PATH)

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df = df.dropna(subset=["timestamp", "symbol"])
    df["date"] = df["timestamp"].dt.date

    # ---- Sentiment scoring -----------------------------------------------
    analyzer = _get_analyzer()

    if analyzer is not None:
        logger.info("Scoring sentiment with VADER…")

        # Combine title + summary for richer signal
        df["_text"] = (
            df.get("title", pd.Series("", index=df.index)).fillna("").astype(str)
            + " "
            + df.get("summary", pd.Series("", index=df.index)).fillna("").astype(str)
        ).str.strip()

        scores = df["_text"].apply(lambda t: _score_text(analyzer, t))
        df["_compound"] = scores.apply(lambda s: s["compound"])
        df["_pos"]      = scores.apply(lambda s: s["pos"])
        df["_neg"]      = scores.apply(lambda s: s["neg"])
        df["_neu"]      = scores.apply(lambda s: s["neu"])
    else:
        logger.warning("No VADER — sentiment will be 0.0 for all articles")
        df["_compound"] = 0.0
        df["_pos"] = 0.0
        df["_neg"] = 0.0
        df["_neu"] = 1.0

    # ---- Daily aggregation per symbol -----------------------------------
    logger.info("Aggregating news by symbol and date")

    agg_df = (
        df.groupby(["symbol", "display_symbol", "market_type", "date"], as_index=False)
        .agg(
            news_count            = ("_compound", "count"),
            sentiment_score       = ("_compound", "mean"),
            sentiment_positive    = ("_pos",      "mean"),
            sentiment_negative    = ("_neg",      "mean"),
            sentiment_neutral     = ("_neu",      "mean"),
            sentiment_std         = ("_compound", "std"),
            sentiment_max         = ("_compound", "max"),
            sentiment_min         = ("_compound", "min"),
        )
        .fillna({"sentiment_std": 0.0})
    )

    # Enforce schema columns (only keep what schema declares)
    schema_cols = GOLD_NEWS_AGGREGATES_COLUMNS
    existing = [c for c in schema_cols if c in agg_df.columns]
    agg_df = agg_df[existing]

    output_dir = Path(GOLD_NEWS_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    agg_df.to_parquet(GOLD_NEWS_FILE, index=False)

    logger.info(
        f"Gold news aggregates written",
        extra={"path": GOLD_NEWS_FILE, "rows": len(agg_df)},
    )
    return agg_df


if __name__ == "__main__":
    df = build_gold_news()
    print(f"\n✅ Gold news built: {len(df)} rows")
    print(df.head(10).to_string(index=False))