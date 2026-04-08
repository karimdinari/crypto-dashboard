print("Starting bootstrap check...")

try:
    from app.config.assets import CRYPTO_ASSETS
    print("Assets loaded")
except Exception as e:
    print("Assets not ready yet (expected in Phase 1)")

try:
    from app.config.settings import COINGECKO_API
    print("Settings loaded")
except Exception:
    print("Settings not ready yet (expected in Phase 1)")

try:
    from app.config.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Logger working")
except Exception:
    print("Logger not ready yet (expected in Phase 1)")

print("Project structure ready")