"""
BTC Direction Model Trainer
============================
Full training pipeline:
    - Load BTC dataset
    - Build target
    - Build features
    - Run walk-forward for 3 models
    - Select best
    - Save artifact
"""

from __future__ import annotations

import json
import joblib
from pathlib import Path

from app.ml.direction.dataset import load_btc_dataset, build_direction_target
from app.ml.direction.features import build_features, select_feature_columns
from app.ml.direction.models import build_model
from app.ml.direction.backtest import walk_forward_backtest
from app.ml.direction.config import MODEL_CANDIDATES
from app.config.logging_config import get_logger


logger = get_logger(__name__)

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def train_direction_model():
    logger.info("Loading BTC dataset")
    df = load_btc_dataset()
    print("Rows after load:", len(df))

    logger.info("Building target")
    df = build_direction_target(df)
    print("Rows after target:", len(df))

    logger.info("Building features")
    df = build_features(df)
    print("Rows after features:", len(df))


    feature_cols = select_feature_columns(df)

    results = {}

    for model_name in MODEL_CANDIDATES:
        logger.info(f"Running walk-forward for {model_name}")

        metrics = walk_forward_backtest(
            df,
            feature_cols,
            lambda: build_model(model_name),
        )

        results[model_name] = metrics
        logger.info(
            f"{model_name} accuracy: {metrics['accuracy']:.4f}"
        )
        logger.info(
            f"{model_name} "
            f"acc={metrics['accuracy']:.4f}, "
            f"precision={metrics['precision_up']:.4f}, "
            f"recall={metrics['recall_up']:.4f}, "
            f"f1={metrics['f1']:.4f}"
        )

    # Select best by accuracy
    best_model_name = max(
        results,
        key=lambda m: results[m]["accuracy"]
    )

    logger.info(f"Best model: {best_model_name}")

    # Retrain best model on full dataset
    best_model = build_model(best_model_name)
    best_model.fit(df[feature_cols], df["target"])

    model_path = ARTIFACT_DIR / "btc_direction_model.pkl"
    joblib.dump(best_model, model_path)

    metadata = {
        "model_type": best_model_name,
        "accuracy": results[best_model_name]["accuracy"],
        "precision_up": results[best_model_name]["precision_up"],
        "recall_up": results[best_model_name]["recall_up"],
        "f1": results[best_model_name]["f1"],
        "features_used": feature_cols,
    }

    with open(ARTIFACT_DIR / "btc_model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("Class distribution:")
    print(df["target"].value_counts(normalize=True))

    print(df["target"].value_counts())
    print(df["target"].value_counts(normalize=True))
    
    logger.info("Model training complete")
    return metadata


if __name__ == "__main__":
    train_direction_model()