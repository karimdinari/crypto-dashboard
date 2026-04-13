"""
Feature Summary Viewer
Shows exactly what features were created in an organized way.
"""

import pandas as pd
from pathlib import Path

from backend.app.features.market_features import build_all_features, get_feature_summary


def show_feature_comparison():
    """Show before/after feature engineering"""
    
    print("\n" + "="*80)
    print("FEATURE ENGINEERING SUMMARY")
    print("="*80)
    
    # Load Silver data (before features)
    from backend.app.config.settings import SILVER_PATH
    silver_path = Path(SILVER_PATH) / "market_data" / "data.parquet"
    df_silver = pd.read_parquet(silver_path)
    
    # Build all features
    df_gold = build_all_features()
    
    # Compare
    print(f"\n📊 DATA COMPARISON:")
    print(f"   Silver (raw):     {len(df_silver.columns):2d} columns")
    print(f"   Gold (features):  {len(df_gold.columns):2d} columns")
    print(f"   New features:     {len(df_gold.columns) - len(df_silver.columns):2d} features added")
    
    # Show what's in Silver
    print(f"\n📦 SILVER COLUMNS (Original Data):")
    for i, col in enumerate(sorted(df_silver.columns), 1):
        print(f"   {i:2d}. {col}")
    
    # Show new features by category
    summary = get_feature_summary(df_gold)
    
    print(f"\n🔥 NEW FEATURES CREATED:")
    
    categories = {
        'price': 'PRICE FEATURES',
        'technical': 'TECHNICAL INDICATORS',
        'volume': 'VOLUME FEATURES',
        'time': 'TIME FEATURES',
        'cross_asset': 'CROSS-ASSET FEATURES',
        'lag': 'LAG FEATURES (Historical Values)'
    }
    
    for key, title in categories.items():
        features = summary.get(key, [])
        if features:
            print(f"\n   {title} ({len(features)}):")
            for i, feat in enumerate(features, 1):
                print(f"      {i:2d}. {feat}")
    
    # Show sample data for Bitcoin
    print("\n" + "="*80)
    print("SAMPLE DATA (Bitcoin - Last 5 Days)")
    print("="*80)
    
    btc = df_gold[df_gold['symbol'] == 'bitcoin'].tail(5)
    
    # Show different feature groups
    show_sample_by_category(btc)


def show_sample_by_category(df):
    """Show sample data organized by feature type"""
    
    # 1. Basic Info
    print("\n📌 BASIC INFO:")
    cols = ['timestamp', 'symbol', 'close', 'volume']
    print(df[cols].to_string(index=False))
    
    # 2. Price Features
    print("\n💰 PRICE FEATURES:")
    cols = [c for c in df.columns if c in ['returns', 'price_diff', 'ma7', 'ma14', 'ma30', 'ema7', 'ema14', 'volatility']]
    if cols:
        print(df[['timestamp'] + cols].to_string(index=False))
    
    # 3. Technical Indicators
    print("\n📈 TECHNICAL INDICATORS:")
    cols = [c for c in df.columns if c in ['rsi', 'macd', 'macd_signal', 'bb_position', 'atr', 'roc']]
    if cols:
        print(df[['timestamp'] + cols].to_string(index=False))
    
    # 4. Volume Features
    print("\n📊 VOLUME FEATURES:")
    cols = [c for c in df.columns if c in ['volume_change', 'volume_ma7', 'relative_volume', 'vwap']]
    if cols:
        print(df[['timestamp'] + cols].to_string(index=False))
    
    # 5. Time Features
    print("\n🕐 TIME FEATURES:")
    cols = [c for c in df.columns if c in ['day_of_week', 'month', 'quarter', 'is_weekend', 'is_month_end']]
    if cols:
        print(df[['timestamp'] + cols].to_string(index=False))
    
    # 6. Cross-Asset Features
    print("\n🔗 CROSS-ASSET FEATURES (Crypto only):")
    cols = [c for c in df.columns if c in ['btc_correlation', 'btc_dominance', 'beta']]
    if cols:
        print(df[['timestamp'] + cols].to_string(index=False))
    
    # 7. Lag Features (sample)
    print("\n⏪ LAG FEATURES (Historical):")
    cols = [c for c in df.columns if c in ['close_lag_1', 'close_lag_7', 'returns_lag_1', 'volume_lag_1']]
    if cols:
        print(df[['timestamp', 'close'] + cols].to_string(index=False))


def show_feature_statistics():
    """Show statistics about features"""
    
    df = build_all_features()
    
    print("\n" + "="*80)
    print("FEATURE STATISTICS")
    print("="*80)
    
    # Get Bitcoin data
    btc = df[df['symbol'] == 'bitcoin'].copy()
    
    feature_groups = {
        'Price Features': ['returns', 'price_diff', 'ma7', 'ma30', 'volatility'],
        'Technical Indicators': ['rsi', 'macd', 'bb_position', 'atr', 'roc'],
        'Volume Features': ['volume_change', 'relative_volume', 'vwap'],
    }
    
    for group_name, features in feature_groups.items():
        print(f"\n📊 {group_name.upper()}:")
        
        existing = [f for f in features if f in btc.columns]
        if not existing:
            continue
            
        stats = btc[existing].describe()
        print(stats.to_string())


def compare_assets():
    """Compare features across different assets"""
    
    df = build_all_features()
    
    print("\n" + "="*80)
    print("ASSET COMPARISON (Latest Values)")
    print("="*80)
    
    # Get latest for each asset
    latest = df.sort_values('timestamp').groupby('symbol').tail(1)
    
    # Select interesting columns
    cols = [
        'symbol', 'close', 'returns', 'volatility', 
        'rsi', 'btc_correlation', 'btc_dominance'
    ]
    
    # Only show columns that exist
    cols = [c for c in cols if c in latest.columns]
    
    print(latest[cols].to_string(index=False))
    
    print("\n💡 Insights:")
    if 'volatility' in latest.columns:
        print(f"   Highest volatility: {latest.loc[latest['volatility'].idxmax(), 'symbol']}")
    if 'rsi' in latest.columns:
        overbought = latest[latest['rsi'] > 70]
        if not overbought.empty:
            print(f"   Overbought (RSI > 70): {overbought['symbol'].tolist()}")
        oversold = latest[latest['rsi'] < 30]
        if not oversold.empty:
            print(f"   Oversold (RSI < 30): {oversold['symbol'].tolist()}")


if __name__ == "__main__":
    
    # 1. Show comprehensive feature summary
    show_feature_comparison()
    
    # 2. Show statistics
    show_feature_statistics()
    
    # 3. Compare assets
    compare_assets()
    
    print("\n" + "="*80)
    print("✅ DONE - All features visualized!")
    print("="*80 + "\n")