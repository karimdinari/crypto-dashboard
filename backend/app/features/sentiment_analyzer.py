"""
Sentiment Analyzer — FinBERT only
===================================
Uses ProsusAI/finbert (HuggingFace) to score financial news.
100% free, runs locally, no API key required.
Model downloads once (~440 MB) to ~/.cache/huggingface/ on first run.

Usage:
    from app.features.sentiment_analyzer import SentimentAnalyzer

    analyzer = SentimentAnalyzer()

    # Single text
    result = analyzer.score("Bitcoin surges to new all-time high")
    # -> {"label": "positive", "score": 0.94, "compound": 0.94}

    # DataFrame  (adds 4 columns in-place)
    df = analyzer.score_dataframe(df, text_col="title", summary_col="summary")

Columns added to DataFrame:
    sentiment_label    : "positive" | "neutral" | "negative"
    sentiment_score    : confidence of the predicted label  (0–1)
    sentiment_compound : signed score  (-1 to +1)
                          positive -> 0 to +1
                          neutral  -> ~0
                          negative -> -1 to 0
    sentiment_model    : always "finbert"
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

_FINBERT_MODEL = "ProsusAI/finbert"

# Maps FinBERT label -> compound sign
_LABEL_SIGN: dict[str, float] = {
    "positive": 1.0,
    "neutral":  0.0,
    "negative": -1.0,
}


class SentimentAnalyzer:
    """
    Financial news sentiment scorer backed by FinBERT.

    Args:
        batch_size: Number of texts per FinBERT inference call.
                    32 is a safe default for CPU; raise to 64+ on GPU.
    """

    def __init__(self, batch_size: int = 32) -> None:
        self._batch_size = batch_size
        self._pipe = self._load_pipeline()

    # ------------------------------------------------------------------
    # Loader
    # ------------------------------------------------------------------

    def _load_pipeline(self):
        try:
            from transformers import pipeline  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "transformers is not installed.\n"
                "Run:  pip install transformers torch"
            ) from exc

        logger.info("Loading FinBERT pipeline — first run downloads ~440 MB to ~/.cache/huggingface/")
        pipe = pipeline(
            "text-classification",
            model=_FINBERT_MODEL,
            tokenizer=_FINBERT_MODEL,
            top_k=1,
            truncation=True,
            max_length=512,
        )
        logger.info("FinBERT loaded successfully.")
        return pipe

    # ------------------------------------------------------------------
    # Single-text scoring
    # ------------------------------------------------------------------

    def score(self, text: str) -> dict[str, Any]:
        """
        Score a single text string.

        Returns:
            {
                "label":    "positive" | "neutral" | "negative",
                "score":    float (0-1),
                "compound": float (-1 to +1),
                "model":    "finbert",
            }
        """
        if not isinstance(text, str) or not text.strip():
            return {"label": "neutral", "score": 0.0, "compound": 0.0, "model": "finbert"}

        return self._run_finbert(text[:512])

    # ------------------------------------------------------------------
    # DataFrame scoring
    # ------------------------------------------------------------------

    def score_dataframe(
        self,
        df: pd.DataFrame,
        text_col: str = "title",
        summary_col: str | None = "summary",
    ) -> pd.DataFrame:
        """
        Add sentiment columns to a news DataFrame.

        FinBERT scores the concatenation of title + summary (if available).
        Title and summary are joined with '. ' so FinBERT sees a single
        coherent sentence rather than two truncated halves.

        Args:
            df:          Input DataFrame -- must contain text_col.
            text_col:    Column with the headline / title.
            summary_col: Optional column with the article summary.
                         Pass None to score title only.

        Returns:
            New DataFrame with four added columns:
                sentiment_label, sentiment_score,
                sentiment_compound, sentiment_model
        """
        if text_col not in df.columns:
            raise ValueError(f"Column '{text_col}' not found in DataFrame.")

        df = df.copy()

        # Build one combined string per row
        texts: list[str] = []
        for _, row in df.iterrows():
            title = str(row.get(text_col, "") or "").strip()
            summary = ""
            if summary_col and summary_col in df.columns:
                summary = str(row.get(summary_col, "") or "").strip()
            combined = f"{title}. {summary}" if summary else title
            texts.append(combined[:512])   # FinBERT max 512 tokens

        results = self._run_finbert_batch(texts)

        df["sentiment_label"]    = [r["label"]    for r in results]
        df["sentiment_score"]    = [r["score"]    for r in results]
        df["sentiment_compound"] = [r["compound"] for r in results]
        df["sentiment_model"]    = "finbert"

        logger.info(
            "FinBERT scoring complete",
            extra={
                "rows":     len(df),
                "positive": (df["sentiment_label"] == "positive").sum(),
                "neutral":  (df["sentiment_label"] == "neutral").sum(),
                "negative": (df["sentiment_label"] == "negative").sum(),
            },
        )
        return df

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_finbert(self, text: str) -> dict[str, Any]:
        """Score a single pre-truncated text."""
        try:
            result = self._pipe(text)
            top = result[0][0] if isinstance(result[0], list) else result[0]
            return self._format(top)
        except Exception as exc:
            logger.warning(f"FinBERT inference error: {exc} -- returning neutral")
            return {"label": "neutral", "score": 0.0, "compound": 0.0, "model": "finbert"}

    def _run_finbert_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        """Score a list of texts in mini-batches."""
        results: list[dict[str, Any]] = []
        try:
            for start in range(0, len(texts), self._batch_size):
                batch = texts[start : start + self._batch_size]
                raw = self._pipe(batch)
                for item in raw:
                    top = item[0] if isinstance(item, list) else item
                    results.append(self._format(top))
        except Exception as exc:
            logger.warning(f"Batch FinBERT failed ({exc}) -- falling back to row-by-row.")
            results = [self._run_finbert(t) for t in texts]
        return results

    @staticmethod
    def _format(top: dict) -> dict[str, Any]:
        """Convert raw FinBERT output to our standard dict."""
        label    = top["label"].lower()
        score    = round(float(top["score"]), 4)
        compound = round(_LABEL_SIGN.get(label, 0.0) * score, 4)
        return {"label": label, "score": score, "compound": compound, "model": "finbert"}