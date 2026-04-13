"""
Feature engineering package.
Provides modular feature calculation for market data.

Main interface:
    from app.features.market_features import build_all_features
    
    df = build_all_features()  # Creates 50+ features for ML
"""

# Main builder
from backend.app.features.market_features import (
    build_market_features,
    build_minimal_features,
    build_standard_features,
    build_all_features,
    get_feature_summary,
    print_feature_summary,
)

# Individual feature modules (for custom workflows)
from backend.app.features.price_features import (
    calculate_returns,
    calculate_price_diff,
    calculate_moving_averages,
    calculate_ema,
    calculate_volatility,
    add_all_price_features,
)

from backend.app.features.technical_indicators import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_atr,
    calculate_roc,
    calculate_stochastic,
    add_all_technical_indicators,
)

from backend.app.features.volume_features import (
    calculate_volume_change,
    calculate_volume_ma,
    calculate_relative_volume,
    calculate_vwap,
    add_all_volume_features,
)

from backend.app.features.time_features import (
    add_time_features,
    add_cyclical_encoding,
    add_all_time_features,
)

from backend.app.features.cross_asset_features import (
    calculate_btc_correlation,
    calculate_btc_dominance,
    calculate_asset_beta,
    add_all_cross_asset_features,
)

from backend.app.features.lag_features import (
    add_price_lags,
    add_returns_lags,
    add_volume_lags,
    add_volatility_lags,
    add_all_lag_features,
)

__all__ = [
    # Main builders
    'build_market_features',
    'build_minimal_features',
    'build_standard_features',
    'build_all_features',
    'get_feature_summary',
    'print_feature_summary',
    
    # Price features
    'calculate_returns',
    'calculate_price_diff',
    'calculate_moving_averages',
    'calculate_ema',
    'calculate_volatility',
    'add_all_price_features',
    
    # Technical indicators
    'calculate_rsi',
    'calculate_macd',
    'calculate_bollinger_bands',
    'calculate_atr',
    'calculate_roc',
    'calculate_stochastic',
    'add_all_technical_indicators',
    
    # Volume features
    'calculate_volume_change',
    'calculate_volume_ma',
    'calculate_relative_volume',
    'calculate_vwap',
    'add_all_volume_features',
    
    # Time features
    'add_time_features',
    'add_cyclical_encoding',
    'add_all_time_features',
    
    # Cross-asset features
    'calculate_btc_correlation',
    'calculate_btc_dominance',
    'calculate_asset_beta',
    'add_all_cross_asset_features',
    
    # Lag features
    'add_price_lags',
    'add_returns_lags',
    'add_volume_lags',
    'add_volatility_lags',
    'add_all_lag_features',
]