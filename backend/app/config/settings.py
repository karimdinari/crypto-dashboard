import os
from pathlib import Path

from dotenv import load_dotenv


def _load_dotenv_files() -> None:
    """
    Load env files from repo root, then backend/ (backend wins on duplicate keys).
    Uses utf-8-sig so a UTF-8 BOM on the first line does not corrupt variable names.
    """
    here = Path(__file__).resolve()
    backend_root = here.parents[2]
    repo_root = here.parents[3]
    for path in (repo_root / ".env", backend_root / ".env"):
        load_dotenv(path, encoding="utf-8-sig", override=path.parent == backend_root)


_load_dotenv_files()


def _default_project_root() -> str:
    """Repo root (parent of ``backend/``), stable regardless of process cwd."""
    # backend/app/config/settings.py -> parents[3] == repository root
    return str(Path(__file__).resolve().parents[3])


def _default_backend_root() -> str:
    """Directory that contains ``app/`` and typically ``data/`` and on-disk Parquet under ``lakehouse/``."""
    # backend/app/config/settings.py -> parents[2] == backend/
    return str(Path(__file__).resolve().parents[2])

# -------------------------------------------------------------------
# Environment
# -------------------------------------------------------------------
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# -------------------------------------------------------------------
# API base URLs
# -------------------------------------------------------------------
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
# EXCHANGERATE_BASE_URL = "https://api.exchangeratesapi.io"
EXCHANGERATE_BASE_URL = "https://api.frankfurter.app"
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
BINANCE_WS_BASE_URL = "wss://stream.binance.com:9443/ws"
# YFINANCE_ENABLED = True  # informational flag for metals ingestion

# -------------------------------------------------------------------
# API keys
# -------------------------------------------------------------------
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY", "")

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
PROJECT_ROOT = os.getenv("PROJECT_ROOT", _default_project_root())
BACKEND_ROOT = os.getenv("BACKEND_ROOT", _default_backend_root())
# Sample + seed CSVs default to repo-root data/ (e.g. data/seeds/metals). Override with DATA_DIR.
# DATA_DIR = os.getenv("DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
SAMPLE_DATA_PATH = os.path.join(DATA_DIR, "sample")
SEED_DATA_PATH = os.path.join(DATA_DIR, "seeds")

# Default under backend/ so Parquet lands in one place regardless of shell cwd
LAKEHOUSE_DIR = os.getenv("LAKEHOUSE_DIR", os.path.join(BACKEND_ROOT, "lakehouse"))
BRONZE_PATH = os.path.join(LAKEHOUSE_DIR, "bronze")
SILVER_PATH = os.path.join(LAKEHOUSE_DIR, "silver")
GOLD_PATH = os.path.join(LAKEHOUSE_DIR, "gold")

LOGS_DIR = os.path.join(BACKEND_ROOT, "logs")

# -------------------------------------------------------------------
# Kafka
# -------------------------------------------------------------------
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC_MARKET_STREAM = os.getenv("KAFKA_TOPIC_MARKET_STREAM", "market_stream")
KAFKA_TOPIC_NEWS_STREAM = os.getenv("KAFKA_TOPIC_NEWS_STREAM", "news_stream")

# -------------------------------------------------------------------
# MinIO / Object Storage
# -------------------------------------------------------------------
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio123")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

MINIO_BUCKET_BRONZE = os.getenv("MINIO_BUCKET_BRONZE", "bronze")
MINIO_BUCKET_SILVER = os.getenv("MINIO_BUCKET_SILVER", "silver")
MINIO_BUCKET_GOLD = os.getenv("MINIO_BUCKET_GOLD", "gold")

# -------------------------------------------------------------------
# Batch scheduling defaults
# -------------------------------------------------------------------
CRYPTO_BATCH_INTERVAL = "hourly"
FOREX_BATCH_INTERVAL = "daily"
METALS_BATCH_INTERVAL = "daily"
NEWS_BATCH_INTERVAL = "daily"

# -------------------------------------------------------------------
# Streaming defaults
# -------------------------------------------------------------------
STREAM_SYMBOLS = ["BTC/USD", "ETH/USD"]
STREAM_POLL_INTERVAL_SECONDS = int(os.getenv("STREAM_POLL_INTERVAL_SECONDS", "5"))
STREAM_RECONNECT_DELAY_SECONDS = int(os.getenv("STREAM_RECONNECT_DELAY_SECONDS", "5"))

# -------------------------------------------------------------------
# Ingestion defaults
# -------------------------------------------------------------------
DEFAULT_REQUEST_TIMEOUT_SECONDS = int(os.getenv("DEFAULT_REQUEST_TIMEOUT_SECONDS", "30"))
DEFAULT_RETRY_COUNT = int(os.getenv("DEFAULT_RETRY_COUNT", "3"))
DEFAULT_RETRY_BACKOFF_SECONDS = int(os.getenv("DEFAULT_RETRY_BACKOFF_SECONDS", "2"))

# -------------------------------------------------------------------
# Data quality defaults
# -------------------------------------------------------------------
DEFAULT_TIMEZONE = "UTC"
ALLOW_EMPTY_VOLUME_FOR_FOREX = True
ALLOW_EMPTY_VOLUME_FOR_METALS = True