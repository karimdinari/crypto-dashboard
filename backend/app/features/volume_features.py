"""
Volume-based features.
Volume confirms price movements and shows market interest.
"""

import pandas as pd
import numpy as np

from backend.app.config.logging_config import get_logger

logger = get_logger(__name__)


def calculate_volume_change(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate percentage change in volume.
    
    Formula: (volume_t - volume_t-1) / volume_t-1 * 100
    
    Args:
        df: DataFrame with volume data
        
    Returns:
        DataFrame with 'volume_change' column added
        
    Why ML needs this:
        - High volume + price up = strong bullish signal
        - High volume + price down = strong bearish signal
        - Low volume = weak signal, likely false move
        
    Example:
        Yesterday volume: 1M BTC
        Today volume: 2M BTC
        Volume change: +100%
        → Strong signal (2x normal activity)
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    df['volume_change'] = df.groupby('symbol')['volume'].pct_change() * 100
    df['volume_change'] = df['volume_change'].fillna(0)
    
    logger.info("Volume change calculated")
    return df


def calculate_volume_ma(df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    """
    Calculate volume moving average.
    
    Shows "normal" volume level over time.
    
    Args:
        df: DataFrame with volume data
        window: Averaging period (default: 7)
        
    Returns:
        DataFrame with 'volume_ma7' column added
        
    Why ML needs this:
        - Baseline for "normal" volume
        - Used to calculate relative volume
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    col_name = f'volume_ma{window}'
    df[col_name] = df.groupby('symbol')['volume'].transform(
        lambda x: x.rolling(window=window, min_periods=1).mean()
    )
    
    logger.info(f"Volume MA{window} calculated")
    return df


def calculate_relative_volume(df: pd.DataFrame, ma_column: str = 'volume_ma7') -> pd.DataFrame:
    """
    Calculate relative volume (current vs average).
    
    Formula: volume_t / volume_ma
    
    Interpretation:
        - Relative volume = 1.0: Normal volume
        - Relative volume > 1.5: High volume (strong signal)
        - Relative volume < 0.5: Low volume (weak signal)
    
    Args:
        df: DataFrame with volume and volume_ma columns
        ma_column: Volume MA column to compare against
        
    Returns:
        DataFrame with 'relative_volume' column added
        
    Why ML needs this:
        - Normalized volume measure
        - Works across different assets (BTC vs ETH have different volume scales)
        - Key for confirmation of price moves
        
    Example:
        Current volume: 150M
        Average volume: 100M
        Relative volume: 1.5 (50% above normal = strong move)
    """
    df = df.copy()
    
    if ma_column not in df.columns:
        df = calculate_volume_ma(df)
        ma_column = 'volume_ma7'
    
    df['relative_volume'] = df['volume'] / df[ma_column].replace(0, np.nan)
    df['relative_volume'] = df['relative_volume'].fillna(1.0)
    
    logger.info("Relative volume calculated")
    return df


def calculate_vwap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Volume-Weighted Average Price (VWAP).
    
    VWAP = Cumulative(price * volume) / Cumulative(volume)
    
    VWAP shows the "true average price" weighted by volume.
    
    Trading interpretation:
        - Price above VWAP: Bullish, buyers in control
        - Price below VWAP: Bearish, sellers in control
        - VWAP acts as support/resistance
    
    Args:
        df: DataFrame with close and volume data
        
    Returns:
        DataFrame with 'vwap' column added
        
    Why ML needs this:
        - Shows institutional price level
        - Better average than simple MA
        - Key support/resistance indicator
        
    Note:
        Traditional VWAP resets daily, but for daily data we use cumulative.
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    def vwap_per_symbol(group):
        # Cumulative volume-weighted price
        cumsum_vol_price = (group['close'] * group['volume']).cumsum()
        cumsum_vol = group['volume'].cumsum()
        return cumsum_vol_price / cumsum_vol.replace(0, np.nan)
    
    df['vwap'] = df.groupby('symbol').apply(vwap_per_symbol).reset_index(level=0, drop=True)
    df['vwap'] = df['vwap'].fillna(df['close'])
    
    logger.info("VWAP calculated")
    return df


def calculate_volume_price_trend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Volume Price Trend (VPT).
    
    VPT = Previous VPT + (Volume * (price_change / previous_price))
    
    Shows the relationship between volume and price change.
    
    Interpretation:
        - VPT rising: Accumulation (buying pressure)
        - VPT falling: Distribution (selling pressure)
        - VPT divergence from price: Potential reversal
    
    Args:
        df: DataFrame with close and volume data
        
    Returns:
        DataFrame with 'vpt' column added
        
    Why ML needs this:
        - Shows accumulation/distribution
        - Combines volume and price in one metric
        - Good for detecting divergences
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    def vpt_per_symbol(group):
        price_change = group['close'].pct_change()
        vpt = (group['volume'] * price_change).cumsum()
        return vpt
    
    df['vpt'] = df.groupby('symbol').apply(vpt_per_symbol).reset_index(level=0, drop=True)
    df['vpt'] = df['vpt'].fillna(0)
    
    logger.info("Volume Price Trend calculated")
    return df


def add_all_volume_features(df: pd.DataFrame, ma_window: int = 7) -> pd.DataFrame:
    """
    Add all volume-based features at once.
    
    Args:
        df: DataFrame with OHLCV data
        ma_window: Volume MA window (default: 7)
        
    Returns:
        DataFrame with all volume features added
        
    Features added:
        - volume_change
        - volume_ma7 (or custom window)
        - relative_volume
        - vwap
        - vpt
        
    Total: 5 new features
    """
    logger.info("Adding all volume features")
    
    df = calculate_volume_change(df)
    df = calculate_volume_ma(df, window=ma_window)
    df = calculate_relative_volume(df)
    df = calculate_vwap(df)
    df = calculate_volume_price_trend(df)
    
    logger.info("All volume features added")
    return df


# =================================================================
# TESTING
# =================================================================

if __name__ == "__main__":
    """Test volume features"""
    from pathlib import Path
    from app.config.settings import SILVER_PATH
    
    silver_path = Path(SILVER_PATH) / "market_data" / "data.parquet"
    
    if silver_path.exists():
        print("\n" + "="*60)
        print("Testing Volume Features")
        print("="*60)
        
        df = pd.read_parquet(silver_path)
        print(f"\nLoaded {len(df)} rows from Silver")
        
        # Add all volume features
        df = add_all_volume_features(df)
        
        print(f"\n✅ Volume features calculated")
        print(f"\nNew features: volume_change, volume_ma7, relative_volume, vwap, vpt")
        
        # Show sample for Bitcoin
        print(f"\n📊 Sample data (Bitcoin):")
        btc = df[df['symbol'] == 'bitcoin'].tail(5)
        display_cols = ['timestamp', 'close', 'volume', 'volume_change', 'relative_volume', 'vwap']
        print(btc[display_cols].to_string(index=False))
        
    else:
        print(f"❌ Silver data not found at {silver_path}")