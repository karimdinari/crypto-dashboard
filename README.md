# Multi-Market Analytics (Tigre)

Monorepo layout:

| Folder       | Role |
|-------------|------|
| `frontend/` | React + Vite trading terminal UI |
| `backend/`  | Python pipeline: Bronze → Silver → Gold |
| `data/bronze/` | Raw Parquet (`market_data.parquet`, `news.parquet`) |
| `data/silver/` | Clean Parquet (`market_data_clean.parquet`, `news_data_clean.parquet`) |
| `data/gold/` | Features + ML table (`market_features.parquet`, `prediction_dataset.parquet`) |
| `docker-compose.yml` | Phase 4 — local Kafka + Zookeeper |

## Frontend + dashboard API (Phase 5)

Terminal 1 — Parquet API (from `backend/`):

```bash
cd backend
pip install -r requirements.txt
python scripts/run_dashboard_api.py
```

Terminal 2 — UI:

```bash
cd frontend
npm install
npm run dev
```

The app calls `/api/...` (proxied to FastAPI). Without the API, it uses built-in mock data.

## Backend — Bronze → Silver → Gold

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python scripts/run_market_ingestion.py   # Phase 1 → data/bronze/
python scripts/run_silver_pipeline.py    # Phase 2 → data/silver/
python scripts/run_gold_pipeline.py      # Phase 3 → data/gold/
```

**Inspect:** `peek_bronze.py` / `peek_silver.py` / `peek_gold.py` (add `--news`, `--prediction` where applicable).

**Phase 4 (streaming):** `docker compose up -d` at repo root, then `backend/scripts/stream_producer.py` + `stream_consumer.py` → `data/bronze/market_stream.parquet`; optional `run_stream_silver.py` → `market_stream_clean.parquet`. See `backend/README.md`.

## Legacy folders

If `node_modules` or `dist` still exist at the **repository root** after the move, delete them and use only `frontend/node_modules`.


market-pipeline/
├── ingestion/
│   ├── batch/
│   │   ├── coingecko_ingestor.py       # crypto prices via REST
│   │   ├── exchangerate_ingestor.py    # forex rates
│   │   ├── metals_csv_loader.py        # XAU/XAG from CSV
│   │   └── base_ingestor.py            # shared retry logic
│   └── streaming/
│       ├── binance_ws_producer.py      # Binance WS → Kafka
│       ├── kafka_consumer.py           # Kafka → Bronze
│       └── kafka_config.py
│
├── lakehouse/
│   ├── bronze/
│   │   ├── write_bronze.py
│   │   └── schema_bronze.py
│   ├── silver/
│   │   ├── clean_silver.py
│   │   └── schema_silver.py
│   ├── gold/
│   │   ├── build_gold.py
│   │   └── schema_gold.py
│   ├── minio_client.py                 # MinIO / S3 wrapper
│   └── delta_utils.py                  # Delta Lake read/write
│
├── transformations/
│   ├── dbt_project/
│   │   ├── models/
│   │   │   ├── silver_prices.sql
│   │   │   ├── gold_metrics.sql        # MA7, MA30, % change
│   │   │   └── gold_correlation.sql    # cross-asset matrix
│   │   ├── dbt_project.yml
│   │   └── profiles.yml
│   ├── indicators.py                   # MA, RSI, Bollinger
│   ├── volatility.py                   # rolling std dev
│   └── correlation.py                  # Pearson matrix
│
├── orchestration/
│   ├── dags/
│   │   ├── dag_batch_ingest.py         # hourly / daily
│   │   ├── dag_silver_transform.py
│   │   └── dag_gold_build.py
│   └── airflow_config.py
│
├── tests/
│   ├── test_schema_bronze.py           # expected columns present
│   ├── test_clean_silver.py            # nulls removed correctly
│   ├── test_indicators.py              # MA7 calculation
│   ├── test_null_checks.py             # close_price not null
│   └── test_price_range.py             # close > 0, high >= low
│
├── config/
│   ├── settings.py                     # env vars, constants
│   ├── .env.example
│   └── logging_config.py              # structured JSON logs
│
├── infra/
│   ├── docker-compose.yml              # full stack
│   ├── Dockerfile.airflow
│   ├── Dockerfile.api
│   └── kafka-topics.sh                 # topic init script
│
├── requirements.txt
├── README.md
└── .gitignore
