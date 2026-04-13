"""
Core + Advanced features for Gold layer.
Total: 12 features for ML.
"""

import pandas as pd
import numpy as np
from app.config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# CORE FEATURES (7)
# ============================================================================

def calculate_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate percentage returns.
    
    Formula: (close_t - close_t-1) / close_t-1
    
    Example:
        Yesterday: $60,000
        Today: $63,000
        Returns: 0.05 = 5%
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    df['returns'] = df.groupby('symbol')['close'].pct_change()
    df['returns'] = df['returns'].fillna(0)
    
    logger.info("✅ Returns calculated")
    return df


def calculate_price_diff(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate absolute price difference.
    
    Formula: close_t - close_t-1
    
    Example:
        Yesterday: $60,000
        Today: $63,000
        Price diff: $3,000
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    df['price_diff'] = df.groupby('symbol')['close'].diff()
    df['price_diff'] = df['price_diff'].fillna(0)
    
    logger.info("✅ Price difference calculated")
    return df


def calculate_ma7(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate 7-day moving average.
    
    Formula: mean(close over last 7 days)
    
    Use:
        - Short-term trend
        - Price > MA7 = bullish
        - Price < MA7 = bearish
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    df['ma7'] = df.groupby('symbol')['close'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )
    
    logger.info("✅ MA7 calculated")
    return df


def calculate_ma30(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate 30-day moving average.
    
    Formula: mean(close over last 30 days)
    
    Use:
        - Long-term trend
        - MA7 > MA30 = uptrend
        - MA7 < MA30 = downtrend
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    df['ma30'] = df.groupby('symbol')['close'].transform(
        lambda x: x.rolling(window=30, min_periods=1).mean()
    )
    
    logger.info("✅ MA30 calculated")
    return df


def calculate_volatility(df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    """
    Calculate rolling volatility (standard deviation).
    
    Formula: std(returns over window)
    
    Use:
        - Risk measure
        - High volatility = risky/unstable
        - Low volatility = stable
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    # Need returns first
    if 'returns' not in df.columns:
        df = calculate_returns(df)
    
    df['volatility'] = df.groupby('symbol')['returns'].transform(
        lambda x: x.rolling(window=window, min_periods=1).std()
    )
    df['volatility'] = df['volatility'].fillna(0)
    
    logger.info(f"✅ Volatility calculated (window={window})")
    return df


def calculate_volume_change(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate volume change.
    
    Formula: volume_t - volume_t-1
    
    Use:
        - High volume + price up = strong trend
        - Low volume + price up = weak trend
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    df['volume_change'] = df.groupby('symbol')['volume'].diff()
    df['volume_change'] = df['volume_change'].fillna(0)
    
    logger.info("✅ Volume change calculated")
    return df


def calculate_correlation(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """
    Calculate correlation with Bitcoin.
    
    Formula: corr(asset_returns, btc_returns)
    
    Values:
        +1 = moves exactly with BTC
         0 = independent
        -1 = moves opposite to BTC
    
    Use:
        - Diversification
        - Risk assessment
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    # Need returns
    if 'returns' not in df.columns:
        df = calculate_returns(df)
    
    # Check if Bitcoin exists
    if 'bitcoin' not in df['symbol'].values:
        logger.warning("Bitcoin not found, setting correlation to 0")
        df['correlation'] = 0.0
        return df
    
    # Get BTC returns
    btc_returns = df[df['symbol'] == 'bitcoin'][['timestamp', 'returns']].rename(
        columns={'returns': 'btc_returns'}
    )
    df = df.merge(btc_returns, on='timestamp', how='left')
    
    # Calculate rolling correlation
    def rolling_corr(group):
        if group.name == 'bitcoin':
            return pd.Series([1.0] * len(group), index=group.index)
        
        if 'btc_returns' not in group.columns or group['btc_returns'].isna().all():
            return pd.Series([0.0] * len(group), index=group.index)
        
        return group['returns'].rolling(window=window, min_periods=10).corr(group['btc_returns'])
    
    df['correlation'] = df.groupby('symbol', group_keys=False).apply(rolling_corr)
    df['correlation'] = df['correlation'].fillna(0)
    
    df = df.drop('btc_returns', axis=1, errors='ignore')
    
    logger.info(f"✅ Correlation calculated (window={window})")
    return df


# ============================================================================
# ADVANCED FEATURES (5)
# ============================================================================

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate Relative Strength Index (RSI).
    
    RSI measures if asset is overbought or oversold.
    
    Range: 0-100
        RSI > 70 → Overbought (price may drop)
        RSI < 30 → Oversold (price may rise)
        RSI = 50 → Neutral
    
    Formula:
        1. Calculate gains and losses
        2. RS = Average Gain / Average Loss
        3. RSI = 100 - (100 / (1 + RS))
    
    Args:
        df: DataFrame with close prices
        period: Lookback period (default: 14)
        
    Returns:
        DataFrame with 'rsi' column added
        
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
    
    logger.info(f"✅ RSI calculated (period={period})")
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
        - macd: Fast EMA - Slow EMA
        - macd_signal: EMA of MACD
        - macd_histogram: MACD - Signal
    
    Trading signals:
        - MACD crosses above signal → Bullish (buy)
        - MACD crosses below signal → Bearish (sell)
        - Histogram growing → Momentum increasing
    
    Args:
        df: DataFrame with close prices
        fast: Fast EMA period (default: 12)
        slow: Slow EMA period (default: 26)
        signal: Signal line period (default: 9)
        
    Returns:
        DataFrame with macd, macd_signal, macd_histogram columns
        
    Example:
        MACD = 500, Signal = 300
        → Bullish (MACD above signal)
        → Histogram = 200 (positive momentum)
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
    
    logger.info(f"✅ MACD calculated (fast={fast}, slow={slow}, signal={signal})")
    return df


def calculate_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract day of week from timestamp.
    
    Values:
        0 = Monday
        1 = Tuesday
        2 = Wednesday
        3 = Thursday
        4 = Friday
        5 = Saturday
        6 = Sunday
    
    Use:
        - Capture weekly patterns
        - Monday effect (often negative)
        - Friday effect (often positive)
    
    Args:
        df: DataFrame with timestamp column
        
    Returns:
        DataFrame with 'day_of_week' column added
        
    Example:
        Markets often behave differently on Mondays vs Fridays
    """
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    
    logger.info("✅ Day of week calculated")
    return df


def calculate_volume_ma7(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate 7-day volume moving average.
    
    Formula: mean(volume over last 7 days)
    
    Use:
        - Baseline for "normal" volume
        - Required for relative_volume calculation
    
    Args:
        df: DataFrame with volume data
        
    Returns:
        DataFrame with 'volume_ma7' column added
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    df['volume_ma7'] = df.groupby('symbol')['volume'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )
    
    logger.info("✅ Volume MA7 calculated")
    return df


def calculate_relative_volume(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate relative volume (current vs average).
    
    Formula: volume / volume_ma7
    
    Interpretation:
        1.0 = Normal volume
        1.5 = 50% above normal (strong signal)
        0.5 = 50% below normal (weak signal)
    
    Use:
        - Confirm price movements
        - High relative_volume + price up = strong bullish signal
        - Low relative_volume + price up = weak signal
    
    Args:
        df: DataFrame with volume and volume_ma7
        
    Returns:
        DataFrame with 'relative_volume' column added
        
    Example:
        Average volume: 30B
        Today volume: 45B
        Relative volume: 1.5 (50% above normal = strong)
    """
    df = df.copy()
    
    # Need volume_ma7 first
    if 'volume_ma7' not in df.columns:
        df = calculate_volume_ma7(df)
    
    df['relative_volume'] = df['volume'] / df['volume_ma7'].replace(0, np.nan)
    df['relative_volume'] = df['relative_volume'].fillna(1.0)
    
    logger.info("✅ Relative volume calculated")
    return df


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def add_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all 12 features to DataFrame.
    
    Core features (7):
        1. returns - % price change
        2. price_diff - absolute price change
        3. ma7 - 7-day moving average
        4. ma30 - 30-day moving average
        5. volatility - rolling standard deviation
        6. volume_change - volume difference
        7. correlation - correlation with BTC
    
    Advanced features (5):
        8. rsi - overbought/oversold indicator
        9. macd - momentum indicator (+ signal + histogram)
        10. day_of_week - temporal patterns
        11. volume_ma7 - volume baseline
        12. relative_volume - normalized volume
    
    Total: 12 features (actually 14 with macd components)
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with all features added
    """
    logger.info("="*70)
    logger.info("Starting feature engineering (12 features)")
    logger.info("="*70)
    
    # Core features
    logger.info("\n📊 Adding CORE features (7)...")
    df = calculate_returns(df)
    df = calculate_price_diff(df)
    df = calculate_ma7(df)
    df = calculate_ma30(df)
    df = calculate_volatility(df)
    df = calculate_volume_change(df)
    df = calculate_correlation(df)
    
    # Advanced features
    logger.info("\n🔥 Adding ADVANCED features (5)...")
    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_day_of_week(df)
    df = calculate_volume_ma7(df)
    df = calculate_relative_volume(df)
    
    logger.info("\n✅ All features added successfully!")
    logger.info("="*70)
    
    return df


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    """Test feature calculations"""
    from pathlib import Path
    from app.config.settings import SILVER_PATH
    
    silver_path = Path(SILVER_PATH) / "market_data" / "data.parquet"
    
    if silver_path.exists():
        print("\n" + "="*70)
        print("TESTING SIMPLE FEATURES")
        print("="*70)
        
        df = pd.read_parquet(silver_path)
        print(f"\nLoaded {len(df)} rows from Silver")
        
        # Add all features
        df = add_all_features(df)
        
        print(f"\n✅ Features calculated: {len(df.columns)} total columns")
        
        # Show feature list
        core_features = ['returns', 'price_diff', 'ma7', 'ma30', 'volatility', 'volume_change', 'correlation']
        advanced_features = ['rsi', 'macd', 'macd_signal', 'macd_histogram', 'day_of_week', 'volume_ma7', 'relative_volume']
        
        print(f"\n📊 CORE features ({len(core_features)}):")
        for i, feat in enumerate(core_features, 1):
            status = "✅" if feat in df.columns else "❌"
            print(f"   {i}. {status} {feat}")
        
        print(f"\n🔥 ADVANCED features ({len(advanced_features)}):")
        for i, feat in enumerate(advanced_features, 1):
            status = "✅" if feat in df.columns else "❌"
            print(f"   {i}. {status} {feat}")
        
        # Show sample
        print(f"\n📈 Sample data (Bitcoin, last 3 rows):")
        btc = df[df['symbol'] == 'bitcoin'].tail(3)
        
        sample_cols = ['timestamp', 'close', 'returns', 'ma7', 'ma30', 'volatility', 'rsi', 'macd', 'relative_volume']
        print(btc[sample_cols].to_string(index=False))
        
    else:
        print(f"❌ Silver data not found at {silver_path}")