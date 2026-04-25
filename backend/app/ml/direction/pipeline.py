"""
ML Pipeline Runner v3 — News-Aware
=====================================
Orchestrates the full ML lifecycle:
    Phase 0 — (Optional) Rebuild Gold ML dataset (market + news join)
    Phase 1 — Train news-aware XGBoost ensemble per symbol
    Phase 2 — Walk-forward backtests
    Phase 3 — Save combined summary to models/pipeline_summary.json

Run from backend/:
    python -m app.ml.direction.pipeline
    python -m app.ml.direction.pipeline --rebuild-gold
    python -m app.ml.direction.pipeline --skip-backtest
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from app.config.logging_config import get_logger
from app.ml.direction.trainer import ML_MODELS_DIR, GOLD_ML_FILE, GOLD_MARKET_FILE, train_all_crypto
from app.ml.direction.backtest import backtest_all_crypto

logger = get_logger(__name__)


def run_ml_pipeline(
    gold_path: Path | None = None,
    skip_backtest: bool = False,
    rebuild_gold_ml: bool = False,
) -> dict[str, Any]:
    """
    Full ML pipeline v3:
        Phase 0 — (Optional) Rebuild Gold ML dataset (market + news join)
        Phase 1 — Train XGBoost classifiers per symbol
        Phase 2 — Walk-forward backtest
        Phase 3 — Save combined summary

    Args:
        gold_path:       Override gold data path (defaults to ml_dataset → market fallback).
        skip_backtest:   Skip backtesting phase.
        rebuild_gold_ml: If True, rebuild gold/ml_dataset before training.

    Returns:
        Combined results dict with training + backtest metrics.
    """
    # ---- Phase 0: Rebuild Gold ML dataset (optional) --------------------
    if rebuild_gold_ml:
        logger.info("=" * 60)
        logger.info("ML Pipeline — Phase 0: Rebuild Gold ML Dataset")
        logger.info("=" * 60)
        try:
            from app.etl.gold.build_gold_ml_dataset import build_gold_ml_dataset
            build_gold_ml_dataset()
            logger.info("Gold ML dataset rebuilt")
        except Exception as exc:
            logger.warning(f"Gold ML dataset rebuild failed: {exc} — continuing with existing data")

    # ---- Phase 1: Training ----------------------------------------------
    logger.info("=" * 60)
    logger.info("ML Pipeline — Phase 1: Training (v3 news-aware)")
    logger.info("=" * 60)

    training_results = train_all_crypto(gold_path)

    # ---- Phase 2: Backtesting -------------------------------------------
    backtest_results: dict[str, Any] = {}
    if not skip_backtest:
        logger.info("=" * 60)
        logger.info("ML Pipeline — Phase 2: Backtesting")
        logger.info("=" * 60)
        try:
            effective_path = gold_path or (GOLD_ML_FILE if GOLD_ML_FILE.exists() else GOLD_MARKET_FILE)
            backtest_results = backtest_all_crypto(effective_path)
        except Exception as exc:
            logger.error("Backtest failed", extra={"error": str(exc)})

    # ---- Phase 3: Combined summary --------------------------------------
    combined: dict[str, Any] = {}
    for symbol in training_results:
        tr = training_results[symbol]
        bt = backtest_results.get(symbol, {})
        combined[symbol] = {
            "training": {
                "accuracy":                 tr.get("test_accuracy"),
                "f1_macro":                 tr.get("test_f1_macro"),
                "n_train":                  tr.get("n_train"),
                "n_test":                   tr.get("n_test"),
                "cv_metrics":               tr.get("cv_metrics", {}),
                "label_distribution":       tr.get("label_distribution", {}),
                "feature_importances":      tr.get("feature_importances", []),
                "news_features_selected":   tr.get("news_features_selected", []),
                "news_feature_importances": tr.get("news_feature_importances", []),
                "error":                    tr.get("error"),
            },
            "backtest": {
                "metrics":    bt.get("metrics", {}),
                "n_oos_bars": bt.get("n_oos_bars"),
            } if bt else None,
        }

    summary = {
        "pipeline_ran_at":  pd.Timestamp.now(tz="UTC").isoformat(),
        "pipeline_version": "v3.0-news-aware",
        "gold_path": str(gold_path or (GOLD_ML_FILE if GOLD_ML_FILE.exists() else GOLD_MARKET_FILE)),
        "symbols":          list(combined.keys()),
        "results":          combined,
    }

    summary_path = ML_MODELS_DIR / "pipeline_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str))

    logger.info(
        "ML Pipeline complete",
        extra={"symbols": list(combined.keys()), "summary_path": str(summary_path)},
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
    import argparse

    parser = argparse.ArgumentParser(description="ML Pipeline v3 — News-Aware")
    parser.add_argument("--rebuild-gold", action="store_true",
                        help="Rebuild gold/ml_dataset before training")
    parser.add_argument("--skip-backtest", action="store_true",
                        help="Skip backtesting phase")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("ML Pipeline v3.0 — News-Aware Training + Backtest")
    print("=" * 70 + "\n")

    summary = run_ml_pipeline(
        rebuild_gold_ml=args.rebuild_gold,
        skip_backtest=args.skip_backtest,
    )

    print("\n📊 Pipeline Results:")
    for symbol, data in summary["results"].items():
        tr = data["training"]
        bt = data.get("backtest")
        if tr.get("error"):
            print(f"\n  ❌ {symbol}: {tr['error']}")
            continue
        news_sel = tr.get("news_features_selected") or []
        print(f"\n  ✅ {symbol}")
        print(f"     Training  → acc={tr['accuracy']:.3f}, f1={tr['f1_macro']:.3f}")
        print(f"     News feats selected: {len(news_sel)} — {news_sel[:3]}")
        if bt and bt.get("metrics"):
            m = bt["metrics"]
            print(
                f"     Backtest  → ret={m.get('total_return', 0):+.2%}, "
                f"alpha={m.get('alpha', 0):+.2%}, "
                f"sharpe={m.get('sharpe', 0):.2f}"
            )

    print(f"\n✅ Summary saved to: {ML_MODELS_DIR / 'pipeline_summary.json'}")