"""
Volatility calculation.
Measures price volatility using rolling standard deviation.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from app.config.logging_config import get_logger

logger = get_logger(__name__)


def calculate_volatility(
    df: pd.DataFrame,
    column: str = "returns",
    window: int = 7,
    output_name: str = "volatility"
) -> pd.DataFrame:
    """
    Calculate rolling volatility (standard deviation of returns).
    
    Volatility = std(returns over last N periods)
    
    High volatility = price swings wildly
    Low volatility = price is stable
    
    Args:
        df: DataFrame with returns data
        column: Column to calculate volatility from (default: 'returns')
        window: Rolling window size (default: 7 days)
        output_name: Name for output column
        
    Returns:
        DataFrame with volatility column added
    """
    df = df.copy()
    df = df.sort_values(["symbol", "timestamp"])
    
    # Calculate rolling standard deviation
    df[output_name] = df.groupby("symbol")[column].transform(
        lambda x: x.rolling(window=window, min_periods=1).std()
    )
    
    logger.info(
        f"Volatility calculated",
        extra={
            "column": column,
            "window": window,
            "new_col": output_name
        }
    )
    
    return df


def calculate_volatility_multiple_windows(
    df: pd.DataFrame,
    column: str = "returns",
    windows: list[int] = [7, 14, 30]
) -> pd.DataFrame:
    """
    Calculate volatility for multiple time windows.
    
    Args:
        df: DataFrame with returns
        column: Column to calculate from
        windows: List of window sizes
        
    Returns:
        DataFrame with multiple volatility columns
    """
    df = df.copy()
    
    for window in windows:
        output_name = f"volatility_{window}d"
        df = calculate_volatility(df, column=column, window=window, output_name=output_name)
    
    logger.info(
        f"Multiple volatilities calculated",
        extra={"windows": windows}
    )
    
    return df


if __name__ == "__main__":
    # Test volatility calculation
    from pathlib import Path
    from app.config.settings import SILVER_PATH
    from app.features.indicators import calculate_returns
    
    silver_path = Path(SILVER_PATH) / "market_data" / "data.parquet"
    
    if silver_path.exists():
        df = pd.read_parquet(silver_path)
        print(f"\n📊 Loaded {len(df)} rows from Silver")
        
        # Need returns first
        df = calculate_returns(df)
        
        # Calculate volatility
        df = calculate_volatility(df, window=7)
        
        print(f"\n✅ Volatility calculated")
        print(f"\nSample data for bitcoin:")
        btc = df[df['symbol'] == 'bitcoin'].head(10)
        print(btc[['timestamp', 'close', 'returns', 'volatility']])
    else:
        print(f"❌ Silver data not found at {silver_path}")