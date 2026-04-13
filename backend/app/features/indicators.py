"""
Market indicators calculation.
Includes returns, price differences, and moving averages.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from backend.app.config.logging_config import get_logger

logger = get_logger(__name__)


def calculate_returns(df: pd.DataFrame, column: str = "close") -> pd.DataFrame:
    """
    Calculate percentage returns for each symbol.
    
    Returns = (price_t - price_t-1) / price_t-1 * 100
    
    Args:
        df: DataFrame with price data
        column: Column name to calculate returns from (default: 'close')
        
    Returns:
        DataFrame with 'returns' column added
    """
    df = df.copy()
    df = df.sort_values(["symbol", "timestamp"])
    
    df["returns"] = df.groupby("symbol")[column].pct_change() * 100
    
    logger.info(
        "Returns calculated",
        extra={"column": column, "new_col": "returns"}
    )
    
    return df


def calculate_price_diff(df: pd.DataFrame, column: str = "close") -> pd.DataFrame:
    """
    Calculate absolute price difference from previous period.
    
    Price Diff = price_t - price_t-1
    
    Args:
        df: DataFrame with price data
        column: Column name to calculate difference from
        
    Returns:
        DataFrame with 'price_diff' column added
    """
    df = df.copy()
    df = df.sort_values(["symbol", "timestamp"])
    
    df["price_diff"] = df.groupby("symbol")[column].diff()
    
    logger.info(
        "Price difference calculated",
        extra={"column": column, "new_col": "price_diff"}
    )
    
    return df


def calculate_moving_average(
    df: pd.DataFrame,
    column: str = "close",
    window: int = 7,
    output_name: str = None
) -> pd.DataFrame:
    """
    Calculate simple moving average (SMA) for each symbol.
    
    MA = mean(price over last N periods)
    
    Args:
        df: DataFrame with price data
        column: Column to calculate MA from
        window: Number of periods for MA
        output_name: Name for output column (default: f'ma{window}')
        
    Returns:
        DataFrame with MA column added
    """
    df = df.copy()
    df = df.sort_values(["symbol", "timestamp"])
    
    if output_name is None:
        output_name = f"ma{window}"
    
    df[output_name] = df.groupby("symbol")[column].transform(
        lambda x: x.rolling(window=window, min_periods=1).mean()
    )
    
    logger.info(
        f"Moving average MA{window} calculated",
        extra={"column": column, "window": window, "new_col": output_name}
    )
    
    return df


def calculate_ma7(df: pd.DataFrame, column: str = "close") -> pd.DataFrame:
    """
    Calculate 7-period moving average.
    
    Args:
        df: DataFrame with price data
        column: Column to calculate MA from
        
    Returns:
        DataFrame with 'ma7' column added
    """
    return calculate_moving_average(df, column=column, window=7, output_name="ma7")


def calculate_ma30(df: pd.DataFrame, column: str = "close") -> pd.DataFrame:
    """
    Calculate 30-period moving average.
    
    Args:
        df: DataFrame with price data
        column: Column to calculate MA from
        
    Returns:
        DataFrame with 'ma30' column added
    """
    return calculate_moving_average(df, column=column, window=30, output_name="ma30")


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all market indicators at once.
    
    Calculates:
    - Returns (percentage change)
    - Price difference (absolute change)
    - MA7 (7-period moving average)
    - MA30 (30-period moving average)
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with all indicator columns added
    """
    logger.info("Calculating all market indicators")
    
    df = calculate_returns(df)
    df = calculate_price_diff(df)
    df = calculate_ma7(df)
    df = calculate_ma30(df)
    
    logger.info(
        "All indicators calculated",
        extra={
            "total_rows": len(df),
            "new_columns": ["returns", "price_diff", "ma7", "ma30"]
        }
    )
    
    return df


if __name__ == "__main__":
    # Test with sample data
    from pathlib import Path
    from app.config.settings import SILVER_PATH
    
    silver_path = Path(SILVER_PATH) / "market_data" / "data.parquet"
    
    if silver_path.exists():
        df = pd.read_parquet(silver_path)
        print(f"\n📊 Loaded {len(df)} rows from Silver")
        
        df = calculate_all_indicators(df)
        
        print(f"\n✅ All indicators calculated")
        print(f"New columns: {['returns', 'price_diff', 'ma7', 'ma30']}")
        print(f"\nSample data for bitcoin:")
        btc = df[df['symbol'] == 'bitcoin'].head(10)
        print(btc[['timestamp', 'close', 'returns', 'price_diff', 'ma7', 'ma30']])
    else:
        print(f"❌ Silver data not found at {silver_path}")