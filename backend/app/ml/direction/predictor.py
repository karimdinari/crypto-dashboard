"""
BTC Direction Predictor
========================
Loads trained model and produces BUY / SELL / HOLD signal.
"""

from __future__ import annotations

import json
import joblib
from pathlib import Path

from app.ml.direction.dataset import load_btc_dataset, build_direction_target
from app.ml.direction.features import build_features, select_feature_columns
from app.ml.direction.config import BUY_THRESHOLD, SELL_THRESHOLD
from app.config.logging_config import get_logger

logger = get_logger(__name__)

ARTIFACT_DIR = Path(__file__).parent / "artifacts"


def predict_latest():
    """
    Generate latest BTC signal.
    """

    model_path = ARTIFACT_DIR / "btc_direction_model.pkl"
    metadata_path = ARTIFACT_DIR / "btc_model_metadata.json"

    if not model_path.exists():
        raise FileNotFoundError("Model not trained. Run trainer first.")

    model = joblib.load(model_path)

    # Load latest BTC data
    df = load_btc_dataset()
    df = build_direction_target(df)
    df = build_features(df)

    feature_cols = select_feature_columns(df)

    latest_row = df.iloc[-1:]

    prob_up = model.predict_proba(latest_row[feature_cols])[0][1]

    # Signal logic
    if prob_up >= BUY_THRESHOLD:
        signal = "BUY"
    elif prob_up <= SELL_THRESHOLD:
        signal = "SELL"
    else:
        signal = "HOLD"

    # Load metadata
    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    result = {
        "symbol": "BTC/USD",
        "prediction_date": str(latest_row["timestamp"].values[0]),
        "signal": signal,
        "probability_up": round(float(prob_up), 4),
        "model_type": metadata["model_type"],
        "walk_forward_accuracy": round(metadata["accuracy"], 4),
    }

    logger.info("Generated BTC signal", extra=result)

    return result


if __name__ == "__main__":
    print(predict_latest())