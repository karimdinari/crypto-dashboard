"""
Main market feature builder.
Combines all feature engineering steps into one function.
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import Optional

from app.config.logging_config import get_logger
from app.config.settings import SILVER_PATH

from app.features.indicators import calculate_all_indicators
from app.features.volatility import calculate_volatility

logger = get_logger(__name__)


def build_market_features(
    df: Optional[pd.DataFrame] = None,
    silver_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Build complete market feature dataset from Silver market data.
    
    This is the main function Person 1 provides to Person 2.
    
    Steps:
    1. Load Silver market data (if not provided)
    2. Calculate returns
    3. Calculate price differences
    4. Calculate MA7 and MA30
    5. Calculate volatility
    6. Return enriched DataFrame
    
    Args:
        df: Optional DataFrame (if already loaded)
        silver_path: Optional path to Silver market data
        
    Returns:
        DataFrame with all market features added
    """
    # Load data if not provided
    if df is None:
        if silver_path is None:
            silver_path = Path(SILVER_PATH) / "market_data" / "data.parquet"
        
        logger.info(f"Loading Silver market data from {silver_path}")
        df = pd.read_parquet(silver_path)
    
    logger.info(
        "Building market features",
        extra={"input_rows": len(df), "input_cols": len(df.columns)}
    )
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort by symbol and timestamp
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    # Calculate all indicators
    df = calculate_all_indicators(df)
    
    # Calculate volatility (needs returns first)
    df = calculate_volatility(df, column="returns", window=7, output_name="volatility")
    
    # Fill NaN values for first rows (where rolling windows don't have enough data)
    # Forward fill is common for time series
    df = df.fillna(method='ffill')
    
    # If still NaN (first row), fill with 0
    df = df.fillna(0)
    
    logger.info(
        "Market features built successfully",
        extra={
            "output_rows": len(df),
            "output_cols": len(df.columns),
            "new_features": ["returns", "price_diff", "ma7", "ma30", "volatility"]
        }
    )
    
    return df


if __name__ == "__main__":
    # Test the complete feature builder
    print("\n" + "="*60)
    print("Testing Market Feature Builder")
    print("="*60 + "\n")
    
    df = build_market_features()
    
    print(f"✅ Market features built")
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print(f"\nColumns: {list(df.columns)}")
    
    print(f"\n📊 Sample data (Bitcoin):")
    btc = df[df['symbol'] == 'bitcoin'].head(10)
    print(btc[['timestamp', 'close', 'returns', 'price_diff', 'ma7', 'ma30', 'volatility']].to_string())
    
    print(f"\n📊 Sample data (EUR/USD):")
    eur = df[df['symbol'] == 'EURUSD'].head(10)
    print(eur[['timestamp', 'close', 'returns', 'price_diff', 'ma7', 'ma30', 'volatility']].to_string())
    
    print(f"\n✅ Feature engineering complete!")