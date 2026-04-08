print("Starting bootstrap check...")

try:
    from app.config.assets import CRYPTO_ASSETS, FOREX_ASSETS, METALS_ASSETS, NEWS_TARGETS
    print(f"Assets loaded: crypto={len(CRYPTO_ASSETS)}, forex={len(FOREX_ASSETS)}, metals={len(METALS_ASSETS)}")
    print(f"News targets loaded: {len(NEWS_TARGETS)}")
except Exception as e:
    print(f"Assets import failed: {e}")

try:
    from app.config.settings import COINGECKO_BASE_URL, EXCHANGERATE_BASE_URL, FINNHUB_BASE_URL
    print("Settings loaded")
    print("CoinGecko:", COINGECKO_BASE_URL)
    print("ExchangeRate:", EXCHANGERATE_BASE_URL)
    print("Finnhub:", FINNHUB_BASE_URL)
except Exception as e:
    print(f"Settings import failed: {e}")

try:
    from app.config.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Logger working")
except Exception as e:
    print(f"Logger not ready yet: {e}")

print("Project structure ready")