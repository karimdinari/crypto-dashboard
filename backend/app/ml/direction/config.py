"""
Direction Prediction Configuration
===================================
All tunable parameters for BTC direction model.
Change values here without touching logic code.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

SYMBOL = "BTC/USD"

# ---------------------------------------------------------------------------
# Walk-forward settings
# ---------------------------------------------------------------------------

# Rolling window size (days)
TRAIN_WINDOW_SIZE = 200   # ~2 years when you have 3 years data

# Minimum samples required to start training
MIN_TRAIN_SAMPLES = 300

# ---------------------------------------------------------------------------
# Signal thresholds
# ---------------------------------------------------------------------------

BUY_THRESHOLD  = 0.60
SELL_THRESHOLD = 0.40

# ---------------------------------------------------------------------------
# Random seeds
# ---------------------------------------------------------------------------

RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Model comparison
# ---------------------------------------------------------------------------

MODEL_CANDIDATES = [
    "logistic",
    "random_forest",
    "xgboost",
]