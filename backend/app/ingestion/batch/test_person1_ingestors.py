"""
Test script for Person 1 ingestors.
Run this to verify CoinGecko and ExchangeRate ingestion works.
"""

import logging
from app.ingestion.batch.coingecko_ingestor import ingest_coingecko
from app.ingestion.batch.exchangerate_ingestor import ingest_exchangerate

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_coingecko():
    """Test CoinGecko ingestion"""
    print("\n" + "="*60)
    print("Testing CoinGecko Ingestor")
    print("="*60)
    
    df = ingest_coingecko()
    
    if df is not None:
        print(f"\n✅ SUCCESS: Retrieved {len(df)} crypto records")
        print("\nData preview:")
        print(df[['symbol', 'display_symbol', 'price', 'market_cap']].to_string())
        return True
    else:
        print("\n❌ FAILED: CoinGecko ingestion returned None")
        return False

def test_exchangerate():
    """Test ExchangeRate ingestion"""
    print("\n" + "="*60)
    print("Testing ExchangeRate Ingestor")
    print("="*60)
    
    df = ingest_exchangerate()
    
    if df is not None:
        print(f"\n✅ SUCCESS: Retrieved {len(df)} forex records")
        print("\nData preview:")
        print(df[['symbol', 'display_symbol', 'exchange_rate']].to_string())
        return True
    else:
        print("\n❌ FAILED: ExchangeRate ingestion returned None")
        return False

if __name__ == "__main__":
    crypto_ok = test_coingecko()
    forex_ok = test_exchangerate()
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"CoinGecko:     {'✅ PASS' if crypto_ok else '❌ FAIL'}")
    print(f"ExchangeRate:  {'✅ PASS' if forex_ok else '❌ FAIL'}")