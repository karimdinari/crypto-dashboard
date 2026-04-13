"""
Price-based features: returns, moving averages, price differences, volatility.
Simple functions - no classes, no inheritance.
"""

import pandas as pd
import numpy as np
from typing import List

from backend.app.config.logging_config import get_logger

logger = get_logger(__name__)


def calculate_returns(df: pd.DataFrame, column: str = 'close') -> pd.DataFrame:
    """
    Calculate percentage returns.
    
    Formula: (price_t - price_t-1) / price_t-1 * 100
    
    Args:
        df: DataFrame with price data
        column: Column to calculate returns from (default: 'close')
        
    Returns:
        DataFrame with 'returns' column added
        
    Example:
        Price yesterday: $100
        Price today: $105
        Returns: 5%
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    df['returns'] = df.groupby('symbol')[column].pct_change() * 100
    df['returns'] = df['returns'].fillna(0)
    
    logger.info("Returns calculated")
    return df


def calculate_price_diff(df: pd.DataFrame, column: str = 'close') -> pd.DataFrame:
    """
    Calculate absolute price difference.
    
    Formula: price_t - price_t-1
    
    Args:
        df: DataFrame with price data
        column: Column to calculate difference from
        
    Returns:
        DataFrame with 'price_diff' column added
        
    Example:
        Price yesterday: $100
        Price today: $105
        Price difference: $5
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    df['price_diff'] = df.groupby('symbol')[column].diff()
    df['price_diff'] = df['price_diff'].fillna(0)
    
    logger.info("Price difference calculated")
    return df


def calculate_moving_averages(
    df: pd.DataFrame,
    column: str = 'close',
    windows: List[int] = [7, 14, 30]
) -> pd.DataFrame:
    """
    Calculate Simple Moving Averages (SMA).
    
    Formula: mean(price over last N periods)
    
    Args:
        df: DataFrame with price data
        column: Column to calculate MA from
        windows: List of window sizes (default: [7, 14, 30])
        
    Returns:
        DataFrame with 'ma7', 'ma14', 'ma30' columns added
        
    Purpose:
        - Smooths price noise
        - Shows trend direction
        - MA7 crossing above MA30 = bullish signal (golden cross)
        - MA7 crossing below MA30 = bearish signal (death cross)
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    for window in windows:
        col_name = f'ma{window}'
        df[col_name] = df.groupby('symbol')[column].transform(
            lambda x: x.rolling(window=window, min_periods=1).mean()
        )
        logger.debug(f"MA{window} calculated")
    
    logger.info(f"Moving averages calculated: {windows}")
    return df


def calculate_ema(
    df: pd.DataFrame,
    column: str = 'close',
    windows: List[int] = [7, 14]
) -> pd.DataFrame:
    """
    Calculate Exponential Moving Averages (EMA).
    
    EMA gives more weight to recent prices than SMA.
    
    Args:
        df: DataFrame with price data
        column: Column to calculate EMA from
        windows: List of window sizes (default: [7, 14])
        
    Returns:
        DataFrame with 'ema7', 'ema14' columns added
        
    Why EMA vs MA:
        - EMA reacts faster to price changes
        - Better for volatile assets like crypto
        - SMA is smoother but slower to respond
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    for window in windows:
        col_name = f'ema{window}'
        df[col_name] = df.groupby('symbol')[column].transform(
            lambda x: x.ewm(span=window, adjust=False).mean()
        )
        logger.debug(f"EMA{window} calculated")
    
    logger.info(f"Exponential moving averages calculated: {windows}")
    return df


def calculate_volatility(
    df: pd.DataFrame,
    returns_column: str = 'returns',
    window: int = 7
) -> pd.DataFrame:
    """
    Calculate rolling volatility (standard deviation of returns).
    
    Formula: std(returns over last N periods)
    
    Args:
        df: DataFrame with returns data
        returns_column: Column to calculate volatility from (default: 'returns')
        window: Rolling window size (default: 7)
        
    Returns:
        DataFrame with 'volatility' column added
        
    Interpretation:
        - High volatility (>5% for crypto): Price is unstable, risky
        - Low volatility (<1% for forex): Price is stable
        
    Why ML needs this:
        - Risk measure
        - High volatility → need wider stop-losses
        - Predicts potential breakouts
        - Volatility tends to cluster (high vol periods continue)
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    df['volatility'] = df.groupby('symbol')[returns_column].transform(
        lambda x: x.rolling(window=window, min_periods=1).std()
    )
    df['volatility'] = df['volatility'].fillna(0)
    
    logger.info(f"Volatility calculated (window={window})")
    return df


def add_all_price_features(
    df: pd.DataFrame,
    ma_windows: List[int] = [7, 14, 30],
    ema_windows: List[int] = [7, 14],
    volatility_window: int = 7
) -> pd.DataFrame:
    """
    Add all price-based features at once.
    
    Args:
        df: DataFrame with OHLCV data
        ma_windows: SMA windows
        ema_windows: EMA windows
        volatility_window: Volatility calculation window
        
    Returns:
        DataFrame with all price features added
        
    Features added:
        - returns
        - price_diff
        - ma7, ma14, ma30 (or custom windows)
        - ema7, ema14 (or custom windows)
        - volatility
    """
    logger.info("Adding all price features")
    
    df = calculate_returns(df)
    df = calculate_price_diff(df)
    df = calculate_moving_averages(df, windows=ma_windows)
    df = calculate_ema(df, windows=ema_windows)
    df = calculate_volatility(df, window=volatility_window)
    
    logger.info("All price features added")
    return df


# =================================================================
# TESTING
# =================================================================

if __name__ == "__main__":
    """Test price features with Silver data"""
    from pathlib import Path
    from app.config.settings import SILVER_PATH
    
    silver_path = Path(SILVER_PATH) / "market_data" / "data.parquet"
    
    if silver_path.exists():
        print("\n" + "="*60)
        print("Testing Price Features")
        print("="*60)
        
        df = pd.read_parquet(silver_path)
        print(f"\nLoaded {len(df)} rows from Silver")
        
        # Add all price features
        df = add_all_price_features(df)
        
        print(f"\n✅ Price features calculated")
        print(f"Total columns: {len(df.columns)}")
        print(f"\nNew features: returns, price_diff, ma7, ma14, ma30, ema7, ema14, volatility")
        
        # Show sample for Bitcoin
        print(f"\n📊 Sample data (Bitcoin):")
        btc = df[df['symbol'] == 'bitcoin'].head(10)
        display_cols = ['timestamp', 'close', 'returns', 'price_diff', 'ma7', 'ma30', 'volatility']
        print(btc[display_cols].to_string(index=False))
        
        # Show sample for EUR/USD
        print(f"\n📊 Sample data (EUR/USD):")
        eur = df[df['symbol'] == 'EURUSD'].head(10)
        print(eur[display_cols].to_string(index=False))
        
    else:
        print(f"❌ Silver data not found at {silver_path}")