"""
ML Pipeline Runner
==================
Orchestrates the full ML lifecycle:
    1. Train XGBoost models on Gold-layer features
    2. Run walk-forward backtests
    3. Save summary to models/pipeline_summary.json

Run from backend/:
    python -m app.ml.pipeline

Or import and call:
    from app.ml.pipeline import run_ml_pipeline
    results = run_ml_pipeline()
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from app.config.logging_config import get_logger
from app.ml.direction.trainer import ML_MODELS_DIR, GOLD_MARKET_FILE, train_all_crypto
from app.ml.direction.backtest import backtest_all_crypto

logger = get_logger(__name__)


def run_ml_pipeline(
    gold_path: Path = GOLD_MARKET_FILE,
    skip_backtest: bool = False,
) -> dict[str, Any]:
    """
    Full ML pipeline:
        Phase 1 — Train XGBoost classifiers per symbol
        Phase 2 — Walk-forward backtest
        Phase 3 — Save combined summary

    Returns:
        Combined results dict with training + backtest metrics.
    """
    logger.info("=" * 60)
    logger.info("ML Pipeline — Phase 1: Training")
    logger.info("=" * 60)

    training_results = train_all_crypto(gold_path)

    backtest_results: dict[str, Any] = {}
    if not skip_backtest:
        logger.info("=" * 60)
        logger.info("ML Pipeline — Phase 2: Backtesting")
        logger.info("=" * 60)
        try:
            backtest_results = backtest_all_crypto(gold_path)
        except Exception as exc:
            logger.error("Backtest failed", extra={"error": str(exc)})

    # Combined summary
    combined: dict[str, Any] = {}
    for symbol in training_results:
        tr = training_results[symbol]
        bt = backtest_results.get(symbol, {})
        combined[symbol] = {
            "training": {
                "accuracy": tr.get("test_accuracy"),
                "f1_macro": tr.get("test_f1_macro"),
                "n_train": tr.get("n_train"),
                "n_test": tr.get("n_test"),
                "cv_metrics": tr.get("cv_metrics", {}),
                "label_distribution": tr.get("label_distribution", {}),
                "feature_importances": tr.get("feature_importances", []),
                "error": tr.get("error"),
            },
            "backtest": {
                "metrics": bt.get("metrics", {}),
                "n_oos_bars": bt.get("n_oos_bars"),
            } if bt else None,
        }

    summary = {
        "pipeline_ran_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "gold_path": str(gold_path),
        "symbols": list(combined.keys()),
        "results": combined,
    }

    summary_path = ML_MODELS_DIR / "pipeline_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str))

    logger.info(
        "ML Pipeline complete",
        extra={
            "symbols": list(combined.keys()),
            "summary_path": str(summary_path),
        },
    )
    return summary


def load_pipeline_summary() -> dict[str, Any] | None:
    """Load the latest pipeline summary from disk."""
    path = ML_MODELS_DIR / "pipeline_summary.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ML Pipeline — Full Training + Backtest")
    print("=" * 70 + "\n")

    summary = run_ml_pipeline()

    print("\n📊 Pipeline Results:")
    for symbol, data in summary["results"].items():
        tr = data["training"]
        bt = data.get("backtest")
        if tr.get("error"):
            print(f"\n  ❌ {symbol}: {tr['error']}")
            continue
        print(f"\n  ✅ {symbol}")
        print(f"     Training  → acc={tr['accuracy']:.3f}, f1={tr['f1_macro']:.3f}")
        if bt and bt.get("metrics"):
            m = bt["metrics"]
            print(
                f"     Backtest  → ret={m.get('total_return', 0):+.2%}, "
                f"alpha={m.get('alpha', 0):+.2%}, "
                f"sharpe={m.get('sharpe', 0):.2f}"
            )

    print(f"\n✅ Summary saved to: {ML_MODELS_DIR / 'pipeline_summary.json'}")