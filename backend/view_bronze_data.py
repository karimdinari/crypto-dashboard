"""
Bronze Layer Data Viewer
View and analyze all data collected in the Bronze layer.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_section(text):
    """Print a section divider"""
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-'*60}{Colors.ENDC}")


def format_number(num):
    """Format large numbers with commas"""
    if pd.isna(num):
        return "N/A"
    if num >= 1_000_000_000:
        return f"${num/1_000_000_000:,.2f}B"
    elif num >= 1_000_000:
        return f"${num/1_000_000:,.2f}M"
    elif num >= 1_000:
        return f"${num/1_000:,.2f}K"
    else:
        return f"${num:,.2f}"


def view_crypto_data(base_path):
    """View cryptocurrency price data"""
    print_section("💰 CRYPTOCURRENCY PRICES")
    
    crypto_path = base_path / "crypto_prices" / "data.parquet"
    
    if not crypto_path.exists():
        print(f"{Colors.WARNING}⚠️  No crypto data found at {crypto_path}{Colors.ENDC}")
        return None
    
    try:
        df = pd.read_parquet(crypto_path)
        
        print(f"{Colors.OKGREEN}✅ Found {len(df)} crypto price records{Colors.ENDC}\n")
        
        # Show summary
        print(f"{Colors.BOLD}Data Summary:{Colors.ENDC}")
        print(f"  • Dataset: {crypto_path}")
        print(f"  • Records: {len(df)}")
        print(f"  • Columns: {', '.join(df.columns)}")
        
        # Get latest data for each crypto
        if 'ingestion_time' in df.columns:
            df['ingestion_time'] = pd.to_datetime(df['ingestion_time'])
            latest_df = df.sort_values('ingestion_time').groupby('symbol').tail(1)
            
            print(f"\n{Colors.BOLD}Latest Prices:{Colors.ENDC}")
            for _, row in latest_df.iterrows():
                print(f"\n  {Colors.OKGREEN}{row['display_symbol']}{Colors.ENDC}")
                print(f"    Price:        {format_number(row['price'])}")
                print(f"    Market Cap:   {format_number(row['market_cap'])}")
                print(f"    Volume (24h): {format_number(row['total_volume'])}")
                print(f"    Updated:      {row['ingestion_time']}")
        
        # Show full DataFrame
        print(f"\n{Colors.BOLD}All Records:{Colors.ENDC}")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 30)
        print(df.to_string(index=False))
        
        return df
        
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error reading crypto data: {e}{Colors.ENDC}")
        return None


def view_forex_data(base_path):
    """View forex exchange rate data"""
    print_section("💱 FOREX EXCHANGE RATES")
    
    forex_path = base_path / "forex_rates" / "data.parquet"
    
    if not forex_path.exists():
        print(f"{Colors.WARNING}⚠️  No forex data found at {forex_path}{Colors.ENDC}")
        return None
    
    try:
        df = pd.read_parquet(forex_path)
        
        print(f"{Colors.OKGREEN}✅ Found {len(df)} forex rate records{Colors.ENDC}\n")
        
        # Show summary
        print(f"{Colors.BOLD}Data Summary:{Colors.ENDC}")
        print(f"  • Dataset: {forex_path}")
        print(f"  • Records: {len(df)}")
        print(f"  • Columns: {', '.join(df.columns)}")
        
        # Get latest data for each pair
        if 'ingestion_time' in df.columns:
            df['ingestion_time'] = pd.to_datetime(df['ingestion_time'])
            latest_df = df.sort_values('ingestion_time').groupby('symbol').tail(1)
            
            print(f"\n{Colors.BOLD}Latest Rates:{Colors.ENDC}")
            for _, row in latest_df.iterrows():
                print(f"\n  {Colors.OKGREEN}{row['display_symbol']}{Colors.ENDC}")
                print(f"    Rate:     {row['exchange_rate']:.4f}")
                print(f"    1 {row['base_currency']} = {row['exchange_rate']:.4f} {row['quote_currency']}")
                print(f"    Updated:  {row['ingestion_time']}")
        
        # Show full DataFrame
        print(f"\n{Colors.BOLD}All Records:{Colors.ENDC}")
        print(df.to_string(index=False))
        
        return df
        
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error reading forex data: {e}{Colors.ENDC}")
        return None


def view_metals_data(base_path):
    """View metals price data"""
    print_section("🥇 PRECIOUS METALS PRICES")
    
    metals_path = base_path / "metals_prices" / "data.parquet"
    
    if not metals_path.exists():
        print(f"{Colors.WARNING}⚠️  No metals data found yet{Colors.ENDC}")
        print(f"    (This will be created by Person 2)")
        return None
    
    try:
        df = pd.read_parquet(metals_path)
        print(f"{Colors.OKGREEN}✅ Found {len(df)} metals price records{Colors.ENDC}\n")
        print(df.to_string(index=False))
        return df
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error reading metals data: {e}{Colors.ENDC}")
        return None


def view_news_data(base_path):
    """View news data"""
    print_section("📰 NEWS ARTICLES")
    
    news_path = base_path / "news" / "data.parquet"
    
    if not news_path.exists():
        print(f"{Colors.WARNING}⚠️  No news data found yet{Colors.ENDC}")
        print(f"    (This will be created by Person 2)")
        return None
    
    try:
        df = pd.read_parquet(news_path)
        print(f"{Colors.OKGREEN}✅ Found {len(df)} news articles{Colors.ENDC}\n")
        
        # Show latest 5 articles
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            latest = df.sort_values('timestamp', ascending=False).head(5)
            
            print(f"{Colors.BOLD}Latest News:{Colors.ENDC}")
            for idx, row in latest.iterrows():
                print(f"\n  {Colors.OKGREEN}• {row['title']}{Colors.ENDC}")
                print(f"    Symbol:  {row['symbol']}")
                print(f"    Source:  {row.get('source_name', 'N/A')}")
                print(f"    Time:    {row['timestamp']}")
        
        return df
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error reading news data: {e}{Colors.ENDC}")
        return None


def show_bronze_stats(base_path):
    """Show overall Bronze layer statistics"""
    print_section("📊 BRONZE LAYER STATISTICS")
    
    datasets = {
        'crypto_prices': base_path / 'crypto_prices' / 'data.parquet',
        'forex_rates': base_path / 'forex_rates' / 'data.parquet',
        'metals_prices': base_path / 'metals_prices' / 'data.parquet',
        'news': base_path / 'news' / 'data.parquet',
    }
    
    total_records = 0
    total_size = 0
    
    print(f"{Colors.BOLD}Dataset Status:{Colors.ENDC}\n")
    
    for name, path in datasets.items():
        if path.exists():
            try:
                df = pd.read_parquet(path)
                size_mb = path.stat().st_size / (1024 * 1024)
                total_records += len(df)
                total_size += size_mb
                
                status = f"{Colors.OKGREEN}✅{Colors.ENDC}"
                print(f"  {status} {name:20s} {len(df):>6} records  {size_mb:>8.2f} MB")
            except:
                print(f"  {Colors.FAIL}❌{Colors.ENDC} {name:20s} Error reading file")
        else:
            print(f"  {Colors.WARNING}⚠️ {Colors.ENDC} {name:20s} Not created yet")
    
    print(f"\n{Colors.BOLD}Total:{Colors.ENDC}")
    print(f"  Records: {total_records:,}")
    print(f"  Size:    {total_size:.2f} MB")
    print(f"  Path:    {base_path}")


def export_to_csv(base_path):
    """Export all Bronze data to CSV files"""
    print_section("💾 EXPORT TO CSV")
    
    datasets = ['crypto_prices', 'forex_rates', 'metals_prices', 'news']
    export_dir = Path("bronze_exports")
    export_dir.mkdir(exist_ok=True)
    
    exported = 0
    
    for dataset in datasets:
        parquet_path = base_path / dataset / "data.parquet"
        
        if parquet_path.exists():
            try:
                df = pd.read_parquet(parquet_path)
                csv_path = export_dir / f"{dataset}.csv"
                df.to_csv(csv_path, index=False)
                
                print(f"{Colors.OKGREEN}✅ Exported {dataset} → {csv_path}{Colors.ENDC}")
                print(f"   {len(df)} records")
                exported += 1
            except Exception as e:
                print(f"{Colors.FAIL}❌ Failed to export {dataset}: {e}{Colors.ENDC}")
    
    if exported > 0:
        print(f"\n{Colors.OKGREEN}✅ Exported {exported} datasets to {export_dir}/{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}⚠️  No data to export{Colors.ENDC}")


def main():
    """Main viewer function"""
    print_header("🏛️  BRONZE LAYER DATA VIEWER")
    
    base_path = Path("backend/lakehouse/bronze")
    
    if not base_path.exists():
        print(f"{Colors.FAIL}❌ Bronze layer not found at {base_path}{Colors.ENDC}")
        print(f"{Colors.WARNING}   Run the ingestors first to create data.{Colors.ENDC}")
        sys.exit(1)
    
    # View all datasets
    crypto_df = view_crypto_data(base_path)
    forex_df = view_forex_data(base_path)
    metals_df = view_metals_data(base_path)
    news_df = view_news_data(base_path)
    
    # Show stats
    show_bronze_stats(base_path)
    
    # Ask if user wants to export
    print(f"\n{Colors.BOLD}Export Options:{Colors.ENDC}")
    print("  1. Export all to CSV")
    print("  2. Skip export")
    
    try:
        choice = input(f"\n{Colors.OKCYAN}Enter choice (1 or 2): {Colors.ENDC}").strip()
        if choice == "1":
            export_to_csv(base_path)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Skipping export{Colors.ENDC}")
    
    print_header("✅ VIEWER COMPLETE")


if __name__ == "__main__":
    main()