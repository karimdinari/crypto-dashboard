"""
Time-based features.
Markets show different behavior on different days/months.
"""

import pandas as pd
import numpy as np

from backend.app.config.logging_config import get_logger

logger = get_logger(__name__)


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add temporal features from timestamp.
    
    Markets have time-based patterns:
        - Monday effect: Often negative returns
        - Month-end effect: Institutions rebalance
        - January effect: Tax-loss selling reversal
        - Quarter-end: Portfolio rebalancing
    
    Args:
        df: DataFrame with timestamp column
        
    Returns:
        DataFrame with time features added
        
    Features added:
        - day_of_week (0=Monday, 6=Sunday)
        - day_of_month (1-31)
        - month (1-12)
        - quarter (1-4)
        - is_month_start (0 or 1)
        - is_month_end (0 or 1)
        
    Why ML needs this:
        - Captures cyclical patterns
        - Markets behave differently on Mondays vs Fridays
        - Month-end has institutional flows
        - Quarter-end has rebalancing
        
    Example patterns:
        - Crypto: Weekend volatility often lower
        - Forex: High activity London/NY overlap (time of day)
        - Stocks: Month-end rally
    """
    df = df.copy()
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Extract time components
    df['day_of_week'] = df['timestamp'].dt.dayofweek  # 0=Mon, 6=Sun
    df['day_of_month'] = df['timestamp'].dt.day       # 1-31
    df['month'] = df['timestamp'].dt.month            # 1-12
    df['quarter'] = df['timestamp'].dt.quarter        # 1-4
    
    # Binary flags
    df['is_month_start'] = df['timestamp'].dt.is_month_start.astype(int)
    df['is_month_end'] = df['timestamp'].dt.is_month_end.astype(int)
    
    logger.info("Time features added: day_of_week, day_of_month, month, quarter, is_month_start, is_month_end")
    
    return df


def add_week_of_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add week of year (1-52).
    
    Why ML needs this:
        - Captures yearly seasonality
        - Some weeks have consistent patterns
        
    Args:
        df: DataFrame with timestamp
        
    Returns:
        DataFrame with 'week_of_year' column added
    """
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    df['week_of_year'] = df['timestamp'].dt.isocalendar().week
    
    logger.info("Week of year added")
    return df


def add_is_weekend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add weekend indicator.
    
    Why ML needs this:
        - Crypto: 24/7 but weekend volume different
        - Forex: Closed weekends (gaps)
        - Stocks: Closed weekends
        
    Args:
        df: DataFrame with timestamp
        
    Returns:
        DataFrame with 'is_weekend' column (0 or 1)
    """
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Saturday=5, Sunday=6
    df['is_weekend'] = (df['timestamp'].dt.dayofweek >= 5).astype(int)
    
    logger.info("Weekend indicator added")
    return df


def add_cyclical_encoding(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add cyclical encoding of time features.
    
    Problem with raw time features:
        - month=12 and month=1 are far apart numerically
        - But they're actually close in time (Dec → Jan)
    
    Solution: Cyclical encoding using sin/cos
        - Preserves cyclical nature
        - month=12 and month=1 are close in transformed space
    
    Args:
        df: DataFrame with time features
        
    Returns:
        DataFrame with cyclical encodings added
        
    Features added:
        - day_of_week_sin, day_of_week_cos
        - month_sin, month_cos
        
    Why ML needs this:
        - Better representation of cyclical patterns
        - ML can learn time-based patterns more easily
    """
    df = df.copy()
    
    if 'day_of_week' not in df.columns:
        df = add_time_features(df)
    
    # Day of week (0-6) → cyclical
    df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    
    # Month (1-12) → cyclical
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    
    logger.info("Cyclical time encodings added")
    return df


def add_all_time_features(
    df: pd.DataFrame,
    include_cyclical: bool = True,
    include_week: bool = False
) -> pd.DataFrame:
    """
    Add all time-based features.
    
    Args:
        df: DataFrame with timestamp column
        include_cyclical: Add sin/cos encodings (default: True)
        include_week: Add week_of_year (default: False)
        
    Returns:
        DataFrame with all time features added
        
    Basic features (always added):
        - day_of_week, day_of_month, month, quarter
        - is_month_start, is_month_end
        - is_weekend
        
    Optional features:
        - cyclical encodings (if include_cyclical=True)
        - week_of_year (if include_week=True)
        
    Total: 8-12 features depending on options
    """
    logger.info("Adding all time features")
    
    df = add_time_features(df)
    df = add_is_weekend(df)
    
    if include_cyclical:
        df = add_cyclical_encoding(df)
    
    if include_week:
        df = add_week_of_year(df)
    
    logger.info("All time features added")
    return df


# =================================================================
# TESTING
# =================================================================

if __name__ == "__main__":
    """Test time features"""
    from pathlib import Path
    from app.config.settings import SILVER_PATH
    
    silver_path = Path(SILVER_PATH) / "market_data" / "data.parquet"
    
    if silver_path.exists():
        print("\n" + "="*60)
        print("Testing Time Features")
        print("="*60)
        
        df = pd.read_parquet(silver_path)
        print(f"\nLoaded {len(df)} rows from Silver")
        
        # Add all time features
        df = add_all_time_features(df)
        
        print(f"\n✅ Time features calculated")
        print(f"\nNew features: day_of_week, day_of_month, month, quarter, is_month_start, is_month_end, is_weekend, cyclical encodings")
        
        # Show sample
        print(f"\n📊 Sample data:")
        sample = df.head(5)
        display_cols = ['timestamp', 'day_of_week', 'month', 'quarter', 'is_weekend', 'is_month_end']
        print(sample[display_cols].to_string(index=False))
        
    else:
        print(f"❌ Silver data not found at {silver_path}")