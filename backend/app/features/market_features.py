"""
Simple market feature builder.
Builds 12 core + advanced features for Phase 4.
"""

import pandas as pd
from pathlib import Path
from typing import Optional

from app.config.logging_config import get_logger
from app.config.settings import SILVER_PATH
from app.features.simple_features import add_all_features

logger = get_logger(__name__)


def build_market_features(
    df: Optional[pd.DataFrame] = None,
    silver_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Build Gold market features from Silver data.
    
    Features created (12 total):
    
    CORE (7):
        1. returns - % price change
        2. price_diff - absolute price change
        3. ma7 - 7-day moving average
        4. ma30 - 30-day moving average
        5. volatility - rolling std
        6. volume_change - volume difference
        7. correlation - correlation with BTC
    
    ADVANCED (5):
        8. rsi - overbought/oversold (0-100)
        9. macd - momentum (+ signal + histogram = 3 columns)
        10. day_of_week - temporal patterns (0-6)
        11. volume_ma7 - 7-day volume average
        12. relative_volume - volume vs average
    
    Args:
        df: Optional DataFrame (if already loaded)
        silver_path: Optional path to Silver data
        
    Returns:
        DataFrame with all features
    """
    # Load data
    if df is None:
        if silver_path is None:
            silver_path = Path(SILVER_PATH) / "market_data" / "data.parquet"
        
        logger.info(f"Loading Silver market data from {silver_path}")
        df = pd.read_parquet(silver_path)
    
    initial_cols = len(df.columns)
    logger.info(f"Starting feature engineering: {len(df)} rows, {initial_cols} columns")
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort data
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    # Add all features
    df = add_all_features(df)
    
    # Fill NaN
    df = df.ffill().fillna(0)
    
    # Replace inf
    df = df.replace([float('inf'), float('-inf')], 0)
    
    new_features = len(df.columns) - initial_cols
    
    logger.info(
        f"Feature engineering complete: {len(df)} rows, {len(df.columns)} columns, {new_features} new features"
    )
    
    return df


if __name__ == "__main__":
    """Test feature builder"""
    
    print("\n" + "="*70)
    print("FEATURE BUILDER TEST (12 Features)")
    print("="*70)
    
    # Build features
    df = build_market_features()
    
    print(f"\n✅ Features built:")
    print(f"   Total rows: {len(df)}")
    print(f"   Total columns: {len(df.columns)}")
    
    # List all features
    original = ['symbol', 'display_symbol', 'market_type', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'source', 'ingestion_time']
    new_features = [col for col in df.columns if col not in original]
    
    print(f"\n🔥 NEW FEATURES ({len(new_features)}):")
    for i, feat in enumerate(sorted(new_features), 1):
        print(f"   {i:2d}. {feat}")
    
    # Show sample
    print(f"\n📈 Sample data (Bitcoin, last 3 rows):")
    btc = df[df['symbol'] == 'bitcoin'].tail(3)
    
    sample_cols = ['timestamp', 'close', 'returns', 'ma7', 'rsi', 'macd', 'relative_volume', 'day_of_week']
    print(btc[sample_cols].to_string(index=False))
    
    print("\n" + "="*70)
    print("✅ FEATURE BUILDER WORKS!")
    print("="*70 + "\n")