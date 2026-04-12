"""
Main market feature builder.
Combines all feature engineering steps into one function.
Outputs schema-compliant Gold market features.
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

# Import Gold schema for validation
try:
    from app.etl.schema_gold import GOLD_MARKET_FEATURES_COLUMNS
except ImportError:
    # Fallback if schema_gold.py is in different location
    GOLD_MARKET_FEATURES_COLUMNS = [
        "symbol",
        "display_symbol",
        "market_type",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "returns",
        "price_diff",
        "ma7",
        "ma30",
        "volatility",
        "source",
        "ingestion_time",
    ]


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
    6. Ensure output matches Gold schema
    7. Return enriched DataFrame
    
    Args:
        df: Optional DataFrame (if already loaded)
        silver_path: Optional path to Silver market data
        
    Returns:
        DataFrame with all market features, matching GOLD_MARKET_FEATURES_COLUMNS schema
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
    
    # ✅ ENSURE OUTPUT MATCHES GOLD SCHEMA
    # Select only the columns defined in schema_gold.py
    missing_cols = set(GOLD_MARKET_FEATURES_COLUMNS) - set(df.columns)
    if missing_cols:
        logger.warning(f"Missing columns in output: {missing_cols}")
        # Add missing columns with None/0
        for col in missing_cols:
            df[col] = None
    
    # Select columns in the exact order from schema
    df = df[GOLD_MARKET_FEATURES_COLUMNS]
    
    logger.info(
        "Market features built successfully",
        extra={
            "output_rows": len(df),
            "output_cols": len(df.columns),
            "new_features": ["returns", "price_diff", "ma7", "ma30", "volatility"],
            "schema_compliant": True
        }
    )
    
    return df


def validate_schema(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Validate that output DataFrame matches Gold market features schema.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        (is_valid, missing_or_extra_columns)
    """
    df_cols = set(df.columns)
    schema_cols = set(GOLD_MARKET_FEATURES_COLUMNS)
    
    missing = schema_cols - df_cols
    extra = df_cols - schema_cols
    
    issues = []
    if missing:
        issues.append(f"Missing: {missing}")
    if extra:
        issues.append(f"Extra: {extra}")
    
    is_valid = len(issues) == 0
    
    return is_valid, issues


if __name__ == "__main__":
    # Test the complete feature builder
    print("\n" + "="*60)
    print("Testing Market Feature Builder (Gold Schema Compliant)")
    print("="*60 + "\n")
    
    df = build_market_features()
    
    print(f"✅ Market features built")
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    
    # Validate schema compliance
    is_valid, issues = validate_schema(df)
    
    if is_valid:
        print(f"\n✅ Schema validation: PASSED")
    else:
        print(f"\n⚠️ Schema validation: ISSUES FOUND")
        for issue in issues:
            print(f"   - {issue}")
    
    print(f"\nColumns (in schema order):")
    for i, col in enumerate(df.columns, 1):
        print(f"   {i:2d}. {col}")
    
    print(f"\n📊 Sample data (Bitcoin):")
    btc = df[df['symbol'] == 'bitcoin'].head(5)
    display_cols = ['timestamp', 'close', 'returns', 'price_diff', 'ma7', 'ma30', 'volatility']
    print(btc[display_cols].to_string(index=False))
    
    print(f"\n📊 Sample data (EUR/USD):")
    eur = df[df['symbol'] == 'EURUSD'].head(5)
    print(eur[display_cols].to_string(index=False))
    
    print(f"\n✅ Feature engineering complete and schema-compliant!")