"""
Feature engineering module.
Provides functions to calculate market indicators, volatility, and other features.
"""

from app.features.indicators import (
    calculate_returns,
    calculate_price_diff,
    calculate_moving_average,
    calculate_ma7,
    calculate_ma30,
)

from app.features.volatility import (
    calculate_volatility,
)

from app.features.market_features import (
    build_market_features,
)

__all__ = [
    # Indicators
    "calculate_returns",
    "calculate_price_diff",
    "calculate_moving_average",
    "calculate_ma7",
    "calculate_ma30",
    
    # Volatility
    "calculate_volatility",
    
    # Main builder
    "build_market_features",
]