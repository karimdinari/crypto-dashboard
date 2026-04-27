"""
Batch / row inference hooks.

Replace ``run_inference`` with a real model forward pass once
``model_loader.load_model`` returns an object.
"""

from __future__ import annotations

from typing import Any


def run_inference(features_row: dict[str, float], model: Any = None) -> dict[str, float] | None:
    """
    Return a dict with at least ``prob_up`` and ``prob_down`` in [0, 1] if a model is loaded.

    When ``model`` is ``None``, callers should use :mod:`signal_engine` heuristics instead.
    """
    if model is None:
        return None
    return None
