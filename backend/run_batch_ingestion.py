"""
Run batch ingestion for Person 1 (Crypto + Forex) and write to Bronze.
"""

from app.ingestion.batch.coingecko_ingestor import ingest_coingecko
from app.ingestion.batch.exchangerate_ingestor import ingest_exchangerate
from app.lakehouse.bronze.write_bronze import write_bronze_table
from app.config.logging_config import get_logger

logger = get_logger(__name__)


def run_crypto_ingestion():
    """Ingest crypto data and write to Bronze"""
    logger.info("="*60)
    logger.info("Starting CoinGecko Crypto Ingestion")
    logger.info("="*60)
    
    try:
        # Fetch data
        df = ingest_coingecko()
        
        if df is not None and not df.empty:
            # Write to Bronze
            output_path = write_bronze_table(
                df=df,
                dataset_name="crypto_prices",
                mode="append"
            )
            
            logger.info(f"✅ SUCCESS: Crypto data written to Bronze")
            logger.info(f"   Path: {output_path}")
            logger.info(f"   Records: {len(df)}")
            return True
        else:
            logger.warning("⚠️  No crypto data to write")
            return False
            
    except Exception as e:
        logger.error(f"❌ FAILED: Crypto ingestion error: {e}")
        return False


def run_forex_ingestion():
    """Ingest forex data and write to Bronze"""
    logger.info("="*60)
    logger.info("Starting Frankfurter Forex Ingestion")
    logger.info("="*60)
    
    try:
        # Fetch data
        df = ingest_exchangerate()
        
        if df is not None and not df.empty:
            # Write to Bronze
            output_path = write_bronze_table(
                df=df,
                dataset_name="forex_rates",
                mode="append"
            )
            
            logger.info(f"✅ SUCCESS: Forex data written to Bronze")
            logger.info(f"   Path: {output_path}")
            logger.info(f"   Records: {len(df)}")
            return True
        else:
            logger.warning("⚠️  No forex data to write")
            return False
            
    except Exception as e:
        logger.error(f"❌ FAILED: Forex ingestion error: {e}")
        return False


def main():
    """Run all Person 1 batch ingestion"""
    print("\n" + "="*60)
    print("PERSON 1 BATCH INGESTION - CRYPTO & FOREX")
    print("="*60 + "\n")
    
    results = {
        'crypto': run_crypto_ingestion(),
        'forex': run_forex_ingestion()
    }
    
    # Summary
    print("\n" + "="*60)
    print("INGESTION SUMMARY")
    print("="*60)
    print(f"Crypto: {'✅ SUCCESS' if results['crypto'] else '❌ FAILED'}")
    print(f"Forex:  {'✅ SUCCESS' if results['forex'] else '❌ FAILED'}")
    print("="*60 + "\n")
    
    if all(results.values()):
        print("✅ All ingestions completed successfully!")
        print("\nData saved to:")
        print("  • backend/lakehouse/bronze/crypto_prices/data.parquet")
        print("  • backend/lakehouse/bronze/forex_rates/data.parquet")
        print("\nView the data with: python view_bronze_data.py")
    else:
        print("⚠️  Some ingestions failed. Check logs above.")


if __name__ == "__main__":
    main()