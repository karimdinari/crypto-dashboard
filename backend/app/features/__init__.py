"""
Feature engineering package.
Provides 12 core + advanced features for market data.

Main interface:
    from app.features.market_features import build_market_features
    
    df = build_market_features()  # Creates 12 features for ML

Features created:
    CORE (7):
        - returns, price_diff, ma7, ma30, volatility, volume_change, correlation
    
    ADVANCED (5):
        - rsi, macd, day_of_week, volume_ma7, relative_volume
"""

# Main builder
from app.features.market_features import build_market_features

# Individual feature functions (from simple_features.py)
from app.features.simple_features import (
    # Core features
    calculate_returns,
    calculate_price_diff,
    calculate_ma7,
    calculate_ma30,
    calculate_volatility,
    calculate_volume_change,
    calculate_correlation,
    
    # Advanced features
    calculate_rsi,
    calculate_macd,
    calculate_day_of_week,
    calculate_volume_ma7,
    calculate_relative_volume,
    
    # All-in-one
    add_all_features,
)

__all__ = [
    # Main builder
    'build_market_features',
    
    # Core features (7)
    'calculate_returns',
    'calculate_price_diff',
    'calculate_ma7',
    'calculate_ma30',
    'calculate_volatility',
    'calculate_volume_change',
    'calculate_correlation',
    
    # Advanced features (5)
    'calculate_rsi',
    'calculate_macd',
    'calculate_day_of_week',
    'calculate_volume_ma7',
    'calculate_relative_volume',
    
    # Batch function
    'add_all_features',
]