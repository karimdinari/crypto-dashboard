"""
Load serialized ML models (XGBoost / sklearn / ONNX) when you add artifacts.

Today: returns ``None`` so the API uses the rule-based :mod:`signal_engine` only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_model(artifact_path: Path | None = None) -> Any:
    """
    Load a model from ``artifact_path`` if present.

    Wire your trained file under ``backend/models/`` and set e.g.
    ``MODEL_ARTIFACT_PATH`` in the environment when ready.
    """
    if artifact_path is None or not artifact_path.is_file():
        return None
    # Example for later:
    # import joblib
    # return joblib.load(artifact_path)
    return None
