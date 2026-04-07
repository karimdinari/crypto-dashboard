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
