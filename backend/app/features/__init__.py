"""
Feature engineering package.
Provides market technical features + news sentiment features for Gold layer.

Market interface:
    from app.features.market_features import build_market_features
    df = build_market_features()

News interface:
    from app.features.news_features import build_news_features
    news_df = build_news_features(news_df, market_df=market_df)
"""

# Market features
from app.features.market_features import build_market_features

# News sentiment features
from app.features.news_features import build_news_features, NEWS_FEATURE_COLUMNS

# Individual market feature functions
from app.features.simple_features import (
    calculate_returns,
    calculate_price_diff,
    calculate_ma7,
    calculate_ma30,
    calculate_volatility,
    calculate_volume_change,
    calculate_correlation,
    calculate_rsi,
    calculate_macd,
    calculate_day_of_week,
    calculate_volume_ma7,
    calculate_relative_volume,
    add_all_features,
)

__all__ = [
    # Main builders
    "build_market_features",
    "build_news_features",
    "NEWS_FEATURE_COLUMNS",

    # Core market features (7)
    "calculate_returns",
    "calculate_price_diff",
    "calculate_ma7",
    "calculate_ma30",
    "calculate_volatility",
    "calculate_volume_change",
    "calculate_correlation",

    # Advanced market features (5)
    "calculate_rsi",
    "calculate_macd",
    "calculate_day_of_week",
    "calculate_volume_ma7",
    "calculate_relative_volume",

    # Batch function
    "add_all_features",
]