"""
Rule-based BUY / SELL / HOLD + confidence until a trained model is wired.

Uses Gold-layer style features already exposed to the dashboard.
"""

from __future__ import annotations

from typing import Literal

Prediction = Literal["BUY", "SELL", "HOLD"]


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def signal_from_features(
    *,
    close: float,
    ma7: float,
    ma30: float,
    rsi: float,
    returns: float,
    volatility: float,
) -> tuple[Prediction, float, float, float]:
    """
    Returns ``(prediction, confidence, prob_up, prob_down)``.

    ``confidence`` is a heuristic strength in ``[0.35, 0.92]``.
    """
    trend = (close - ma30) / ma30 if ma30 else 0.0
    short = (close - ma7) / ma7 if ma7 else 0.0

    score = 0.0
    score += 1.4 * trend
    score += 0.6 * short
    score += (rsi - 50.0) / 50.0 * 0.35
    score += returns * 12.0
    score -= min(volatility, 5.0) / 5.0 * 0.15

    if score > 0.18:
        pred: Prediction = "BUY"
    elif score < -0.18:
        pred = "SELL"
    else:
        pred = "HOLD"

    # Map score to pseudo-probabilities
    from math import exp

    eu, ed, eh = exp(score * 2.2), exp(-score * 2.2), exp(-abs(score) * 1.8)
    z = eu + ed + eh
    prob_up = _clamp(eu / z)
    prob_down = _clamp(ed / z)
    confidence = _clamp(0.45 + min(abs(score), 1.2) * 0.35, 0.35, 0.92)

    return pred, confidence, prob_up, prob_down


def top_features_from_row(correlation: float | None) -> list[dict[str, float]]:
    """Lightweight feature importance stand-in for the UI bars."""
    base = [
        ("RSI momentum", 0.22),
        ("Trend vs MA30", 0.2),
        ("Short MA7 pull", 0.16),
        ("Return shock", 0.14),
        ("Volatility regime", 0.12),
    ]
    if correlation is not None:
        base.append(("BTC correlation", min(0.28, max(0.05, abs(correlation) * 0.25))))
    return [{"name": n, "weight": w} for n, w in base[:5]]
