"""
Lag features: historical values.
Essential for time series ML - model needs to see past to predict future.
"""

import pandas as pd
import numpy as np
from typing import List

from backend.app.config.logging_config import get_logger

logger = get_logger(__name__)


def add_price_lags(
    df: pd.DataFrame,
    column: str = 'close',
    lags: List[int] = [1, 2, 3, 7, 14]
) -> pd.DataFrame:
    """
    Add lagged price values.
    
    Lag features = historical values from N periods ago.
    
    Why ML needs this:
        - Time series pattern: past → present → future
        - Model needs historical context
        - close_lag_1 = yesterday's price
        - close_lag_7 = price from 1 week ago
    
    Args:
        df: DataFrame with price data
        column: Column to create lags from (default: 'close')
        lags: List of lag periods (default: [1, 2, 3, 7, 14])
        
    Returns:
        DataFrame with lag columns added
        
    Features added:
        - close_lag_1 (yesterday)
        - close_lag_2 (2 days ago)
        - close_lag_3 (3 days ago)
        - close_lag_7 (1 week ago)
        - close_lag_14 (2 weeks ago)
        
    Example:
        Today: close = $70,000
        close_lag_1 = $69,500 (yesterday)
        close_lag_7 = $68,000 (last week)
        
        ML can learn: "When close > close_lag_7 by >2%, trend is strong"
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    for lag in lags:
        col_name = f'{column}_lag_{lag}'
        df[col_name] = df.groupby('symbol')[column].shift(lag)
    
    # Fill NaN with forward fill (first rows won't have enough history)
    lag_cols = [f'{column}_lag_{lag}' for lag in lags]
    df[lag_cols] = df[lag_cols].fillna(method='ffill')
    
    logger.info(f"Price lags added: {lags}")
    return df


def add_returns_lags(
    df: pd.DataFrame,
    lags: List[int] = [1, 2, 3, 7]
) -> pd.DataFrame:
    """
    Add lagged returns.
    
    Why ML needs this:
        - Captures momentum
        - Past returns predict future returns (momentum effect)
        - returns_lag_1 = yesterday's return
        
    Args:
        df: DataFrame with returns column
        lags: List of lag periods
        
    Returns:
        DataFrame with returns lag columns added
        
    Example:
        Today: returns = +2%
        returns_lag_1 = +3% (yesterday)
        returns_lag_2 = -1% (2 days ago)
        
        ML learns: "Consecutive positive returns → momentum → keep rising"
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    if 'returns' not in df.columns:
        from app.features.price_features import calculate_returns
        df = calculate_returns(df)
    
    for lag in lags:
        col_name = f'returns_lag_{lag}'
        df[col_name] = df.groupby('symbol')['returns'].shift(lag)
    
    # Fill NaN with 0 (no return if no history)
    lag_cols = [f'returns_lag_{lag}' for lag in lags]
    df[lag_cols] = df[lag_cols].fillna(0)
    
    logger.info(f"Returns lags added: {lags}")
    return df


def add_volume_lags(
    df: pd.DataFrame,
    lags: List[int] = [1, 2, 3]
) -> pd.DataFrame:
    """
    Add lagged volume values.
    
    Why ML needs this:
        - Volume patterns predict price moves
        - Increasing volume → trend strengthening
        - volume_lag_1 = yesterday's volume
        
    Args:
        df: DataFrame with volume column
        lags: List of lag periods
        
    Returns:
        DataFrame with volume lag columns added
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    for lag in lags:
        col_name = f'volume_lag_{lag}'
        df[col_name] = df.groupby('symbol')['volume'].shift(lag)
    
    # Fill NaN
    lag_cols = [f'volume_lag_{lag}' for lag in lags]
    df[lag_cols] = df[lag_cols].fillna(method='ffill').fillna(0)
    
    logger.info(f"Volume lags added: {lags}")
    return df


def add_volatility_lags(
    df: pd.DataFrame,
    lags: List[int] = [1, 2, 3]
) -> pd.DataFrame:
    """
    Add lagged volatility values.
    
    Why ML needs this:
        - Volatility clustering: high vol → high vol continues
        - volatility_lag_1 = yesterday's volatility
        
    Args:
        df: DataFrame with volatility column
        lags: List of lag periods
        
    Returns:
        DataFrame with volatility lag columns added
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    if 'volatility' not in df.columns:
        from app.features.price_features import calculate_volatility, calculate_returns
        if 'returns' not in df.columns:
            df = calculate_returns(df)
        df = calculate_volatility(df)
    
    for lag in lags:
        col_name = f'volatility_lag_{lag}'
        df[col_name] = df.groupby('symbol')['volatility'].shift(lag)
    
    lag_cols = [f'volatility_lag_{lag}' for lag in lags]
    df[lag_cols] = df[lag_cols].fillna(0)
    
    logger.info(f"Volatility lags added: {lags}")
    return df


def add_all_lag_features(
    df: pd.DataFrame,
    price_lags: List[int] = [1, 2, 3, 7, 14],
    returns_lags: List[int] = [1, 2, 3, 7],
    volume_lags: List[int] = [1, 2, 3],
    volatility_lags: List[int] = [1, 2, 3]
) -> pd.DataFrame:
    """
    Add all lag features.
    
    Args:
        df: DataFrame with market data
        price_lags: Price lag periods
        returns_lags: Returns lag periods
        volume_lags: Volume lag periods
        volatility_lags: Volatility lag periods
        
    Returns:
        DataFrame with all lag features added
        
    Features added:
        - close_lag_1, close_lag_2, ..., close_lag_14
        - returns_lag_1, returns_lag_2, ..., returns_lag_7
        - volume_lag_1, volume_lag_2, volume_lag_3
        - volatility_lag_1, volatility_lag_2, volatility_lag_3
        
    Total: 17 new features (with default settings)
    
    Why so many lags:
        - Different time horizons capture different patterns
        - lag_1: Short-term (yesterday)
        - lag_7: Medium-term (last week)
        - lag_14: Longer-term (2 weeks ago)
        - ML will learn which lags matter most
    """
    logger.info("Adding all lag features")
    
    df = add_price_lags(df, lags=price_lags)
    df = add_returns_lags(df, lags=returns_lags)
    df = add_volume_lags(df, lags=volume_lags)
    df = add_volatility_lags(df, lags=volatility_lags)
    
    total_lags = len(price_lags) + len(returns_lags) + len(volume_lags) + len(volatility_lags)
    logger.info(f"All lag features added: {total_lags} total")
    
    return df


# =================================================================
# TESTING
# =================================================================

if __name__ == "__main__":
    """Test lag features"""
    from pathlib import Path
    from app.config.settings import SILVER_PATH
    
    silver_path = Path(SILVER_PATH) / "market_data" / "data.parquet"
    
    if silver_path.exists():
        print("\n" + "="*60)
        print("Testing Lag Features")
        print("="*60)
        
        df = pd.read_parquet(silver_path)
        print(f"\nLoaded {len(df)} rows from Silver")
        
        # Add lag features
        df = add_all_lag_features(df)
        
        print(f"\n✅ Lag features calculated")
        print(f"\nNew features: close_lag_1/2/3/7/14, returns_lag_1/2/3/7, volume_lag_1/2/3, volatility_lag_1/2/3")
        
        # Show sample
        print(f"\n📊 Sample data (Bitcoin):")
        btc = df[df['symbol'] == 'bitcoin'].tail(5)
        display_cols = ['timestamp', 'close', 'close_lag_1', 'close_lag_7', 'returns', 'returns_lag_1']
        print(btc[display_cols].to_string(index=False))
        
    else:
        print(f"❌ Silver data not found at {silver_path}")