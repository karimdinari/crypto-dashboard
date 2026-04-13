"""
Technical indicators: RSI, MACD, Bollinger Bands, ATR, ROC, Stochastic.
Advanced features for ML pattern recognition.
"""

import pandas as pd
import numpy as np
from typing import Tuple

from backend.app.config.logging_config import get_logger

logger = get_logger(__name__)


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate Relative Strength Index (RSI).
    
    RSI measures if asset is overbought or oversold.
    
    Range: 0-100
    - RSI > 70: Overbought (price may drop soon)
    - RSI < 30: Oversold (price may rise soon)
    - RSI = 50: Neutral
    
    Formula:
        1. Calculate gains and losses
        2. Average gain / average loss = RS
        3. RSI = 100 - (100 / (1 + RS))
    
    Args:
        df: DataFrame with price data
        period: Lookback period (default: 14)
        
    Returns:
        DataFrame with 'rsi' column added
        
    Why ML needs this:
        - Identifies reversal points
        - Shows momentum strength
        - Works well in ranging markets
        
    Example:
        BTC RSI = 75 → Overbought, might drop
        BTC RSI = 25 → Oversold, might rise
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    def rsi_per_symbol(series):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
        
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)  # Neutral when can't calculate
    
    df['rsi'] = df.groupby('symbol')['close'].transform(rsi_per_symbol)
    
    logger.info(f"RSI calculated (period={period})")
    return df


def calculate_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> pd.DataFrame:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    MACD shows momentum and trend changes.
    
    Components:
        - MACD line: Fast EMA - Slow EMA
        - Signal line: EMA of MACD line
        - Histogram: MACD - Signal
    
    Trading signals:
        - MACD crosses above signal: Bullish (buy signal)
        - MACD crosses below signal: Bearish (sell signal)
        - Histogram growing: Momentum increasing
        - Histogram shrinking: Momentum decreasing
    
    Args:
        df: DataFrame with price data
        fast: Fast EMA period (default: 12)
        slow: Slow EMA period (default: 26)
        signal: Signal line period (default: 9)
        
    Returns:
        DataFrame with 'macd', 'macd_signal', 'macd_histogram' columns
        
    Why ML needs this:
        - Captures trend direction
        - Shows momentum strength
        - Identifies trend reversals
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    def macd_per_symbol(series):
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd': macd_line,
            'macd_signal': signal_line,
            'macd_histogram': histogram
        })
    
    macd_df = df.groupby('symbol')['close'].apply(macd_per_symbol).reset_index(level=0, drop=True)
    
    df['macd'] = macd_df['macd'].values
    df['macd_signal'] = macd_df['macd_signal'].values
    df['macd_histogram'] = macd_df['macd_histogram'].values
    
    logger.info(f"MACD calculated (fast={fast}, slow={slow}, signal={signal})")
    return df


def calculate_bollinger_bands(
    df: pd.DataFrame,
    window: int = 20,
    num_std: int = 2
) -> pd.DataFrame:
    """
    Calculate Bollinger Bands.
    
    Bollinger Bands show volatility and potential price extremes.
    
    Components:
        - Middle band: 20-day SMA
        - Upper band: Middle + (2 * std dev)
        - Lower band: Middle - (2 * std dev)
        - Position: Where price is within bands (0-1)
    
    Interpretation:
        - Price at upper band: Overbought
        - Price at lower band: Oversold
        - Bands narrow: Low volatility (breakout coming)
        - Bands wide: High volatility
    
    Args:
        df: DataFrame with price data
        window: SMA period (default: 20)
        num_std: Number of standard deviations (default: 2)
        
    Returns:
        DataFrame with bb_upper, bb_middle, bb_lower, bb_position columns
        
    Why ML needs this:
        - Shows price extremes
        - Measures volatility
        - Identifies mean reversion opportunities
        - bb_position is normalized (0-1) - great for ML!
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    df['bb_middle'] = df.groupby('symbol')['close'].transform(
        lambda x: x.rolling(window=window, min_periods=1).mean()
    )
    
    df['bb_std'] = df.groupby('symbol')['close'].transform(
        lambda x: x.rolling(window=window, min_periods=1).std()
    )
    
    df['bb_upper'] = df['bb_middle'] + (num_std * df['bb_std'])
    df['bb_lower'] = df['bb_middle'] - (num_std * df['bb_std'])
    
    # Position within bands (0 = at lower, 1 = at upper)
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    df['bb_position'] = df['bb_position'].clip(0, 1).fillna(0.5)
    
    # Drop intermediate column
    df = df.drop('bb_std', axis=1)
    
    logger.info(f"Bollinger Bands calculated (window={window}, std={num_std})")
    return df


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate Average True Range (ATR).
    
    ATR measures market volatility.
    Better than simple std deviation because it accounts for gaps.
    
    True Range = max of:
        - High - Low
        - |High - Previous Close|
        - |Low - Previous Close|
    
    ATR = Average of True Range over N periods
    
    Args:
        df: DataFrame with OHLC data
        period: Averaging period (default: 14)
        
    Returns:
        DataFrame with 'atr' column added
        
    Why ML needs this:
        - Better volatility measure than std dev
        - Accounts for price gaps
        - Used for stop-loss placement
        - High ATR = need wider stops
        
    Example:
        BTC ATR = $2000 → Daily range is about $2000
        EUR/USD ATR = 0.005 → Daily range is about 50 pips
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    # Calculate True Range components
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = abs(df['high'] - df.groupby('symbol')['close'].shift(1))
    df['low_close'] = abs(df['low'] - df.groupby('symbol')['close'].shift(1))
    
    # True Range = max of the three
    df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    
    # ATR = average of True Range
    df['atr'] = df.groupby('symbol')['true_range'].transform(
        lambda x: x.rolling(window=period, min_periods=1).mean()
    )
    
    # Clean up intermediate columns
    df = df.drop(['high_low', 'high_close', 'low_close', 'true_range'], axis=1)
    
    logger.info(f"ATR calculated (period={period})")
    return df


def calculate_roc(df: pd.DataFrame, period: int = 9) -> pd.DataFrame:
    """
    Calculate Rate of Change (ROC).
    
    ROC measures momentum (speed of price change).
    
    Formula: ((price_t - price_t-n) / price_t-n) * 100
    
    Interpretation:
        - ROC > 0: Upward momentum
        - ROC < 0: Downward momentum
        - ROC increasing: Momentum accelerating
        - ROC decreasing: Momentum slowing
    
    Args:
        df: DataFrame with price data
        period: Lookback period (default: 9)
        
    Returns:
        DataFrame with 'roc' column added
        
    Why ML needs this:
        - Captures momentum
        - Shows rate of acceleration
        - Early warning of trend changes
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    df['roc'] = df.groupby('symbol')['close'].transform(
        lambda x: ((x - x.shift(period)) / x.shift(period)) * 100
    )
    df['roc'] = df['roc'].fillna(0)
    
    logger.info(f"ROC calculated (period={period})")
    return df


def calculate_stochastic(
    df: pd.DataFrame,
    k_period: int = 14,
    d_period: int = 3
) -> pd.DataFrame:
    """
    Calculate Stochastic Oscillator.
    
    Shows where current price is relative to recent high/low range.
    
    Components:
        - %K: Current position in range (fast line)
        - %D: SMA of %K (slow line)
    
    Range: 0-100
    - > 80: Overbought
    - < 20: Oversold
    
    Formula:
        %K = ((Close - Low14) / (High14 - Low14)) * 100
        %D = 3-period SMA of %K
    
    Args:
        df: DataFrame with OHLC data
        k_period: Period for %K (default: 14)
        d_period: Period for %D (default: 3)
        
    Returns:
        DataFrame with 'stoch_k', 'stoch_d' columns
        
    Why ML needs this:
        - Identifies overbought/oversold
        - Works well in ranging markets
        - Complements RSI
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    # Rolling high and low
    df['roll_high'] = df.groupby('symbol')['high'].transform(
        lambda x: x.rolling(window=k_period, min_periods=1).max()
    )
    df['roll_low'] = df.groupby('symbol')['low'].transform(
        lambda x: x.rolling(window=k_period, min_periods=1).min()
    )
    
    # %K
    df['stoch_k'] = ((df['close'] - df['roll_low']) / 
                     (df['roll_high'] - df['roll_low'])) * 100
    df['stoch_k'] = df['stoch_k'].fillna(50)
    
    # %D (smoothed %K)
    df['stoch_d'] = df.groupby('symbol')['stoch_k'].transform(
        lambda x: x.rolling(window=d_period, min_periods=1).mean()
    )
    
    # Clean up
    df = df.drop(['roll_high', 'roll_low'], axis=1)
    
    logger.info(f"Stochastic calculated (k={k_period}, d={d_period})")
    return df


def add_all_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all technical indicators at once.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with all technical indicators added
        
    Features added:
        - rsi
        - macd, macd_signal, macd_histogram
        - bb_upper, bb_middle, bb_lower, bb_position
        - atr
        - roc
        - stoch_k, stoch_d
        
    Total: 13 new features
    """
    logger.info("Adding all technical indicators")
    
    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_bollinger_bands(df)
    df = calculate_atr(df)
    df = calculate_roc(df)
    df = calculate_stochastic(df)
    
    logger.info("All technical indicators added")
    return df


# =================================================================
# TESTING
# =================================================================

if __name__ == "__main__":
    """Test technical indicators"""
    from pathlib import Path
    from app.config.settings import SILVER_PATH
    
    silver_path = Path(SILVER_PATH) / "market_data" / "data.parquet"
    
    if silver_path.exists():
        print("\n" + "="*60)
        print("Testing Technical Indicators")
        print("="*60)
        
        df = pd.read_parquet(silver_path)
        print(f"\nLoaded {len(df)} rows from Silver")
        
        # Add all technical indicators
        df = add_all_technical_indicators(df)
        
        print(f"\n✅ Technical indicators calculated")
        print(f"Total columns: {len(df.columns)}")
        print(f"\nNew features: rsi, macd, macd_signal, macd_histogram, bb_upper, bb_middle, bb_lower, bb_position, atr, roc, stoch_k, stoch_d")
        
        # Show sample for Bitcoin
        print(f"\n📊 Sample data (Bitcoin):")
        btc = df[df['symbol'] == 'bitcoin'].tail(5)
        display_cols = ['timestamp', 'close', 'rsi', 'macd', 'bb_position', 'atr', 'roc']
        print(btc[display_cols].to_string(index=False))
        
    else:
        print(f"❌ Silver data not found at {silver_path}")