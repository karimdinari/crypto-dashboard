"""
Cross-asset features: correlations, dominance.
Shows how assets relate to each other.

IMPORTANT: Some features only work if market_cap column exists (crypto data).
"""

import pandas as pd
import numpy as np

from backend.app.config.logging_config import get_logger

logger = get_logger(__name__)


def calculate_btc_correlation(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """
    Calculate rolling correlation with Bitcoin.
    
    Shows how much each asset follows Bitcoin's movement.
    
    Correlation interpretation:
        - 1.0: Perfect positive correlation (moves exactly with BTC)
        - 0.0: No correlation (independent movement)
        - -1.0: Perfect negative correlation (moves opposite to BTC)
    
    Args:
        df: DataFrame with returns for all assets
        window: Rolling window for correlation (default: 30)
        
    Returns:
        DataFrame with 'btc_correlation' column added
        
    Why ML needs this:
        - In crypto, most altcoins follow BTC
        - High BTC correlation → riskier (BTC drops, everything drops)
        - Low correlation → potential diversification
        - Changing correlation → regime change
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    # Need returns column
    if 'returns' not in df.columns:
        logger.warning("Returns column not found, skipping BTC correlation")
        df['btc_correlation'] = 0.0
        return df
    
    # Check if Bitcoin exists in data
    if 'bitcoin' not in df['symbol'].values:
        logger.warning("Bitcoin not found in data, setting btc_correlation to 0")
        df['btc_correlation'] = 0.0
        return df
    
    # Get BTC returns
    btc_data = df[df['symbol'] == 'bitcoin'][['timestamp', 'returns']].rename(
        columns={'returns': 'btc_returns'}
    )
    
    # Merge with all data
    df = df.merge(btc_data, on='timestamp', how='left')
    
    # Calculate rolling correlation for each symbol
    def rolling_corr(group):
        if group.name == 'bitcoin':
            # BTC correlation with itself = 1
            return pd.Series([1.0] * len(group), index=group.index)
        
        # Check if btc_returns exists
        if 'btc_returns' not in group.columns or group['btc_returns'].isna().all():
            return pd.Series([0.0] * len(group), index=group.index)
        
        return group['returns'].rolling(window=window, min_periods=10).corr(group['btc_returns'])
    
    df['btc_correlation'] = df.groupby('symbol', group_keys=False).apply(rolling_corr)
    df['btc_correlation'] = df['btc_correlation'].fillna(0)
    
    # Clean up intermediate column
    df = df.drop('btc_returns', axis=1, errors='ignore')
    
    logger.info(f"BTC correlation calculated (window={window})")
    return df


def calculate_btc_dominance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Bitcoin dominance (BTC market cap / Total crypto market cap).
    
    REQUIRES: market_cap column (only available for crypto data)
    
    BTC dominance shows Bitcoin's influence on the crypto market.
    
    Interpretation:
        - High dominance (>50%): BTC leads, altcoins weak
        - Low dominance (<40%): Altcoin season, money flowing to alts
        - Rising dominance: Flight to safety (BTC)
        - Falling dominance: Risk-on (altcoins)
    
    Args:
        df: DataFrame with market_cap for all crypto assets
        
    Returns:
        DataFrame with 'btc_dominance' column added
        
    Note:
        If market_cap column doesn't exist, sets btc_dominance to 0
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    # Check if market_cap column exists
    if 'market_cap' not in df.columns:
        logger.warning("market_cap column not found, setting btc_dominance to 0 (only available for crypto data)")
        df['btc_dominance'] = 0.0
        return df
    
    # Check if Bitcoin exists
    if 'bitcoin' not in df['symbol'].values:
        logger.warning("Bitcoin not found in data, setting btc_dominance to 0")
        df['btc_dominance'] = 0.0
        return df
    
    # Get BTC market cap
    btc_mcap = df[df['symbol'] == 'bitcoin'][['timestamp', 'market_cap']].rename(
        columns={'market_cap': 'btc_market_cap'}
    )
    
    # Get total crypto market cap (only crypto assets)
    crypto_df = df[df['market_type'] == 'crypto'].copy()
    
    if crypto_df.empty:
        logger.warning("No crypto assets found, setting btc_dominance to 0")
        df['btc_dominance'] = 0.0
        return df
    
    total_mcap = crypto_df.groupby('timestamp')['market_cap'].sum().reset_index()
    total_mcap.columns = ['timestamp', 'total_crypto_mcap']
    
    # Merge
    df = df.merge(btc_mcap, on='timestamp', how='left')
    df = df.merge(total_mcap, on='timestamp', how='left')
    
    # Calculate dominance
    df['btc_dominance'] = (df['btc_market_cap'] / df['total_crypto_mcap']) * 100
    df['btc_dominance'] = df['btc_dominance'].fillna(0)  # Non-crypto or missing data = 0
    
    # Clean up intermediate columns
    df = df.drop(['btc_market_cap', 'total_crypto_mcap'], axis=1, errors='ignore')
    
    logger.info("BTC dominance calculated")
    return df


def calculate_asset_beta(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """
    Calculate beta relative to Bitcoin.
    
    Beta measures volatility relative to a benchmark (here: Bitcoin).
    
    Beta interpretation:
        - Beta = 1.0: Same volatility as BTC
        - Beta > 1.0: More volatile than BTC (riskier)
        - Beta < 1.0: Less volatile than BTC (safer)
    
    Formula:
        Beta = Covariance(asset, BTC) / Variance(BTC)
    
    Args:
        df: DataFrame with returns
        window: Rolling window (default: 30)
        
    Returns:
        DataFrame with 'beta' column added
    """
    df = df.copy()
    df = df.sort_values(['symbol', 'timestamp']).reset_index(drop=True)
    
    if 'returns' not in df.columns:
        logger.warning("Returns column not found, setting beta to 1.0")
        df['beta'] = 1.0
        return df
    
    if 'bitcoin' not in df['symbol'].values:
        logger.warning("Bitcoin not found, setting beta to 1.0")
        df['beta'] = 1.0
        return df
    
    # Get BTC returns
    btc_returns = df[df['symbol'] == 'bitcoin'][['timestamp', 'returns']].rename(
        columns={'returns': 'btc_returns'}
    )
    df = df.merge(btc_returns, on='timestamp', how='left')
    
    # Calculate beta for each symbol
    def calc_beta(group):
        if group.name == 'bitcoin':
            return pd.Series([1.0] * len(group), index=group.index)
        
        if 'btc_returns' not in group.columns or group['btc_returns'].isna().all():
            return pd.Series([1.0] * len(group), index=group.index)
        
        # Rolling covariance / variance
        cov = group['returns'].rolling(window=window, min_periods=10).cov(group['btc_returns'])
        var = group['btc_returns'].rolling(window=window, min_periods=10).var()
        beta = cov / var.replace(0, np.nan)
        
        return beta.fillna(1.0)
    
    df['beta'] = df.groupby('symbol', group_keys=False).apply(calc_beta)
    
    df = df.drop('btc_returns', axis=1, errors='ignore')
    
    logger.info(f"Beta calculated (window={window})")
    return df


def add_all_cross_asset_features(df: pd.DataFrame, correlation_window: int = 30) -> pd.DataFrame:
    """
    Add all cross-asset features.
    
    Args:
        df: DataFrame with market data for all assets
        correlation_window: Window for rolling calculations
        
    Returns:
        DataFrame with cross-asset features added
        
    Features added:
        - btc_correlation (all assets if BTC exists)
        - btc_dominance (crypto only, requires market_cap)
        - beta (all assets if BTC exists)
        
    Total: 3 new features
    
    Note: 
        - If market_cap doesn't exist, btc_dominance will be 0
        - If Bitcoin doesn't exist, correlation/beta will be 0/1
        - For non-crypto assets, features may be 0 or neutral values
    """
    logger.info("Adding all cross-asset features")
    
    df = calculate_btc_correlation(df, window=correlation_window)
    df = calculate_btc_dominance(df)
    df = calculate_asset_beta(df, window=correlation_window)
    
    logger.info("All cross-asset features added")
    return df


# =================================================================
# TESTING
# =================================================================

if __name__ == "__main__":
    """Test cross-asset features"""
    from pathlib import Path
    from app.config.settings import SILVER_PATH
    
    silver_path = Path(SILVER_PATH) / "market_data" / "data.parquet"
    
    if silver_path.exists():
        print("\n" + "="*60)
        print("Testing Cross-Asset Features")
        print("="*60)
        
        df = pd.read_parquet(silver_path)
        print(f"\nLoaded {len(df)} rows from Silver")
        print(f"Columns: {list(df.columns)}")
        
        # Add returns first (needed for correlations)
        from app.features.price_features import calculate_returns
        df = calculate_returns(df)
        
        # Add cross-asset features
        df = add_all_cross_asset_features(df)
        
        print(f"\n✅ Cross-asset features calculated")
        print(f"\nNew features: btc_correlation, btc_dominance, beta")
        
        # Show sample
        print(f"\n📊 Sample data:")
        sample = df.tail(10)
        display_cols = ['timestamp', 'symbol', 'btc_correlation', 'btc_dominance', 'beta']
        display_cols = [col for col in display_cols if col in sample.columns]
        print(sample[display_cols].to_string(index=False))
        
    else:
        print(f"❌ Silver data not found at {silver_path}")