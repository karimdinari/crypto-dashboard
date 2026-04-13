"""
Main feature builder - combines all feature modules.
This is the main interface for feature engineering.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List

from backend.app.config.logging_config import get_logger
from backend.app.config.settings import SILVER_PATH

# Import all feature modules
from backend.app.features.price_features import add_all_price_features
from backend.app.features.technical_indicators import add_all_technical_indicators
from backend.app.features.volume_features import add_all_volume_features
from backend.app.features.time_features import add_all_time_features
from backend.app.features.cross_asset_features import add_all_cross_asset_features
from backend.app.features.lag_features import add_all_lag_features

logger = get_logger(__name__)


def build_market_features(
    df: Optional[pd.DataFrame] = None,
    silver_path: Optional[str] = None,
    # Feature group toggles
    include_price_features: bool = True,
    include_technical_indicators: bool = True,
    include_volume_features: bool = True,
    include_time_features: bool = True,
    include_cross_asset_features: bool = True,
    include_lag_features: bool = True,
    # Feature parameters
    ma_windows: List[int] = [7, 14, 30],
    ema_windows: List[int] = [7, 14],
    volatility_window: int = 7,
    volume_ma_window: int = 7,
    correlation_window: int = 30,
    price_lags: List[int] = [1, 2, 3, 7, 14],
    returns_lags: List[int] = [1, 2, 3, 7],
    volume_lags: List[int] = [1, 2, 3],
    volatility_lags: List[int] = [1, 2, 3],
) -> pd.DataFrame:
    """
    Build complete market feature dataset from Silver market data.
    
    This is the MAIN function that creates all features for ML.
    
    Process:
        1. Load Silver market data
        2. Add price features (returns, MA, EMA, volatility)
        3. Add technical indicators (RSI, MACD, Bollinger, etc.)
        4. Add volume features (volume analysis)
        5. Add time features (day/month patterns)
        6. Add cross-asset features (correlations, dominance)
        7. Add lag features (historical values)
        8. Return feature-rich DataFrame ready for Gold layer
    
    Args:
        df: Optional DataFrame (if already loaded)
        silver_path: Optional path to Silver market data
        
        include_*: Boolean flags to enable/disable feature groups
        
        ma_windows: Moving average windows (default: [7, 14, 30])
        ema_windows: EMA windows (default: [7, 14])
        volatility_window: Volatility calculation window (default: 7)
        volume_ma_window: Volume MA window (default: 7)
        correlation_window: Cross-asset correlation window (default: 30)
        price_lags: Price lag periods (default: [1, 2, 3, 7, 14])
        returns_lags: Returns lag periods (default: [1, 2, 3, 7])
        volume_lags: Volume lag periods (default: [1, 2, 3])
        volatility_lags: Volatility lag periods (default: [1, 2, 3])
        
    Returns:
        DataFrame with all features (45-50 columns)
        
    Example usage:
        # All features (maximum)
        df = build_market_features()
        
        # Only basic features (fast)
        df = build_market_features(
            include_technical_indicators=False,
            include_cross_asset_features=False,
            include_lag_features=False
        )
        
        # Custom configuration
        df = build_market_features(
            ma_windows=[7, 30],  # Only MA7 and MA30
            price_lags=[1, 2, 3]  # Only 3 price lags
        )
    """
    
    # ================================================================
    # STEP 1: LOAD DATA
    # ================================================================
    
    if df is None:
        if silver_path is None:
            silver_path = Path(SILVER_PATH) / "market_data" / "data.parquet"
        
        logger.info(f"Loading Silver market data from {silver_path}")
        df = pd.read_parquet(silver_path)
    
    logger.info(
        "Starting feature engineering",
        extra={
            "input_rows": len(df),
            "input_cols": len(df.columns),
            "symbols": df['symbol'].nunique()
        }
    )
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort by symbol and timestamp (required for rolling calculations)
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    initial_cols = len(df.columns)
    
    # ================================================================
    # STEP 2: PRICE FEATURES
    # ================================================================
    
    if include_price_features:
        logger.info("Adding price features...")
        df = add_all_price_features(
            df,
            ma_windows=ma_windows,
            ema_windows=ema_windows,
            volatility_window=volatility_window
        )
        logger.info(f"✅ Price features added ({len(df.columns) - initial_cols} new columns)")
    
    # ================================================================
    # STEP 3: TECHNICAL INDICATORS
    # ================================================================
    
    if include_technical_indicators:
        logger.info("Adding technical indicators...")
        cols_before = len(df.columns)
        df = add_all_technical_indicators(df)
        logger.info(f"✅ Technical indicators added ({len(df.columns) - cols_before} new columns)")
    
    # ================================================================
    # STEP 4: VOLUME FEATURES
    # ================================================================
    
    if include_volume_features:
        logger.info("Adding volume features...")
        cols_before = len(df.columns)
        df = add_all_volume_features(df, ma_window=volume_ma_window)
        logger.info(f"✅ Volume features added ({len(df.columns) - cols_before} new columns)")
    
    # ================================================================
    # STEP 5: TIME FEATURES
    # ================================================================
    
    if include_time_features:
        logger.info("Adding time features...")
        cols_before = len(df.columns)
        df = add_all_time_features(df, include_cyclical=True)
        logger.info(f"✅ Time features added ({len(df.columns) - cols_before} new columns)")
    
    # ================================================================
    # STEP 6: CROSS-ASSET FEATURES
    # ================================================================
    
    if include_cross_asset_features:
        logger.info("Adding cross-asset features...")
        cols_before = len(df.columns)
        df = add_all_cross_asset_features(df, correlation_window=correlation_window)
        logger.info(f"✅ Cross-asset features added ({len(df.columns) - cols_before} new columns)")
    
    # ================================================================
    # STEP 7: LAG FEATURES
    # ================================================================
    
    if include_lag_features:
        logger.info("Adding lag features...")
        cols_before = len(df.columns)
        df = add_all_lag_features(
            df,
            price_lags=price_lags,
            returns_lags=returns_lags,
            volume_lags=volume_lags,
            volatility_lags=volatility_lags
        )
        logger.info(f"✅ Lag features added ({len(df.columns) - cols_before} new columns)")
    
    # ================================================================
    # STEP 8: FINAL CLEANUP
    # ================================================================
    
    # Fill any remaining NaN values
    # Forward fill for time series continuity
    df = df.fillna(method='ffill')
    
    # If still NaN (first rows), fill with 0
    df = df.fillna(0)
    
    # Replace inf with 0
    df = df.replace([float('inf'), float('-inf')], 0)
    
    total_features = len(df.columns) - initial_cols
    
    logger.info(
        "Feature engineering complete",
        extra={
            "output_rows": len(df),
            "output_cols": len(df.columns),
            "new_features": total_features,
            "symbols": df['symbol'].nunique()
        }
    )
    
    return df


def get_feature_summary(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Get summary of features by category.
    
    Args:
        df: DataFrame with features
        
    Returns:
        Dictionary mapping category to list of feature names
        
    Example:
        summary = get_feature_summary(df)
        print(f"Price features: {summary['price']}")
    """
    
    all_cols = set(df.columns)
    
    # Original columns (from Silver)
    original = {
        'symbol', 'display_symbol', 'market_type', 'timestamp',
        'open', 'high', 'low', 'close', 'volume',
        'source', 'ingestion_time'
    }
    
    # Feature categories
    price_features = [col for col in all_cols if any(x in col for x in ['return', 'price_diff', 'ma', 'ema', 'volatility']) and 'lag' not in col]
    
    technical_features = [col for col in all_cols if any(x in col for x in ['rsi', 'macd', 'bb_', 'atr', 'roc', 'stoch'])]
    
    volume_features = [col for col in all_cols if 'volume' in col and 'lag' not in col and col != 'volume']
    
    time_features = [col for col in all_cols if any(x in col for x in ['day_', 'month', 'quarter', 'week', 'weekend', '_sin', '_cos'])]
    
    cross_asset_features = [col for col in all_cols if any(x in col for x in ['btc_correlation', 'btc_dominance', 'beta'])]
    
    lag_features = [col for col in all_cols if 'lag' in col]
    
    summary = {
        'original': sorted(list(original & all_cols)),
        'price': sorted(price_features),
        'technical': sorted(technical_features),
        'volume': sorted(volume_features),
        'time': sorted(time_features),
        'cross_asset': sorted(cross_asset_features),
        'lag': sorted(lag_features)
    }
    
    return summary


def print_feature_summary(df: pd.DataFrame) -> None:
    """
    Print human-readable feature summary.
    
    Args:
        df: DataFrame with features
    """
    summary = get_feature_summary(df)
    
    print("\n" + "="*70)
    print("FEATURE SUMMARY")
    print("="*70)
    
    for category, features in summary.items():
        if features:
            print(f"\n{category.upper()} ({len(features)} features):")
            for i, feat in enumerate(features, 1):
                print(f"  {i:2d}. {feat}")
    
    total = sum(len(features) for features in summary.values()) - len(summary['original'])
    print("\n" + "="*70)
    print(f"TOTAL NEW FEATURES: {total}")
    print(f"TOTAL COLUMNS: {len(df.columns)}")
    print("="*70 + "\n")


# =================================================================
# PREDEFINED CONFIGURATIONS
# =================================================================

def build_minimal_features(df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Build minimal feature set (fast, for testing).
    
    Features included:
        - Returns, price_diff
        - MA7, MA30
        - Volatility
        - Basic time features
        
    Total: ~15 features
    """
    return build_market_features(
        df=df,
        include_price_features=True,
        include_technical_indicators=False,
        include_volume_features=False,
        include_time_features=True,
        include_cross_asset_features=False,
        include_lag_features=False,
        ma_windows=[7, 30],
        ema_windows=[],
    )


def build_standard_features(df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Build standard feature set (balanced speed/performance).
    
    Features included:
        - All price features
        - RSI, MACD, Bollinger
        - Basic volume features
        - Time features
        - Price and return lags
        
    Total: ~30-35 features
    """
    return build_market_features(
        df=df,
        include_price_features=True,
        include_technical_indicators=True,
        include_volume_features=True,
        include_time_features=True,
        include_cross_asset_features=False,
        include_lag_features=True,
        price_lags=[1, 2, 3, 7],
        returns_lags=[1, 2, 3],
        volume_lags=[1],
        volatility_lags=[1],
    )


def build_all_features(df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Build ALL features (maximum for ML).
    
    Features included:
        - All price features
        - All technical indicators
        - All volume features
        - All time features
        - All cross-asset features
        - All lag features
        
    Total: ~50-60 features
    
    Use this for initial ML training and feature importance analysis.
    """
    return build_market_features(
        df=df,
        include_price_features=True,
        include_technical_indicators=True,
        include_volume_features=True,
        include_time_features=True,
        include_cross_asset_features=True,
        include_lag_features=True,
    )


# =================================================================
# TESTING
# =================================================================

if __name__ == "__main__":
    """
    Test feature engineering with different configurations.
    """
    
    print("\n" + "="*70)
    print("TESTING MARKET FEATURE BUILDER")
    print("="*70)
    
    # Test 1: Minimal features
    print("\n[1/3] Testing MINIMAL features...")
    df_minimal = build_minimal_features()
    print(f"✅ Minimal features: {len(df_minimal.columns)} columns")
    
    # Test 2: Standard features
    print("\n[2/3] Testing STANDARD features...")
    df_standard = build_standard_features()
    print(f"✅ Standard features: {len(df_standard.columns)} columns")
    
    # Test 3: All features
    print("\n[3/3] Testing ALL features...")
    df_all = build_all_features()
    print(f"✅ All features: {len(df_all.columns)} columns")
    
    # Print detailed summary
    print_feature_summary(df_all)
    
    # Show sample data
    print("\n" + "="*70)
    print("SAMPLE DATA (Bitcoin, last 5 rows)")
    print("="*70)
    
    btc = df_all[df_all['symbol'] == 'bitcoin'].tail(5)
    
    # Select interesting columns to display
    display_cols = [
        'timestamp', 'close', 'returns', 'ma7', 'ma30',
        'rsi', 'macd', 'volatility', 'volume_change',
        'day_of_week', 'btc_correlation', 'close_lag_1'
    ]
    
    # Only show columns that exist
    display_cols = [col for col in display_cols if col in btc.columns]
    
    print(btc[display_cols].to_string(index=False))
    
    print("\n" + "="*70)
    print("✅ FEATURE ENGINEERING TEST COMPLETE")
    print("="*70)
    print(f"\n💡 Use build_all_features() to create maximum features for ML")
    print(f"💡 Use build_standard_features() for faster iteration")
    print(f"💡 Use build_minimal_features() for quick testing")
    print("\n")