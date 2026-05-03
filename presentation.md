# Crypto-Dashboard Project Presentation

## Executive Summary

**Crypto-Dashboard** is an enterprise-grade **Data Engineering & Machine Learning platform** that ingests, processes, and analyzes multi-asset market data (cryptocurrencies, forex, metals, news) through a **modern data lakehouse architecture** with real-time streaming capabilities and predictive ML models.

**Key Insight:** From raw market data → refined analytics → actionable trading signals

---

## Project Overview

### What It Does

The platform performs **end-to-end data pipeline orchestration** for financial market analytics:

1. **Real-time Data Ingestion** - Crypto (Binance WebSocket), Forex, Metals, News feeds
2. **Batch Processing** - Daily/hourly aggregations from multiple APIs
3. **Multi-layer Transformation** - Bronze → Silver → Gold (Lakehouse pattern)
4. **Feature Engineering** - 12+ technical indicators (RSI, MACD, Moving Averages)
5. **ML Prediction** - BTC direction prediction (up/down signals)
6. **API Serving** - RESTful endpoints for frontend consumption
7. **Web Dashboard** - Real-time visualization of predictions and market data

### Target Use Cases

- Portfolio managers seeking ML-driven signals
- Traders requiring multi-market correlation analysis
- Fintech platforms needing scalable market analytics
- Data engineers studying modern lakehouse patterns

---

## Technology Stack

### Backend - Python Ecosystem

#### Data Processing & Pipelines
| Component | Purpose |
|-----------|---------|
| **Apache Airflow** | DAG orchestration, job scheduling |
| **Pandas** | Data transformation & analysis |
| **PyArrow** | Parquet serialization, columnar storage |
| **DuckDB** | Lightweight SQL analytics on Parquet |
| **Apache Kafka** | Message streaming (Zookeeper + Kafka broker) |

#### Machine Learning
| Component | Purpose |
|-----------|---------|
| **scikit-learn** | Logistic Regression, Random Forest pipelines |
| **XGBoost** | Gradient boosting classifier |
| **Transformers + PyTorch** | FinBERT sentiment analysis |
| **NumPy/SciPy** | Numerical computing, statistics |

#### API & Web Services
| Component | Purpose |
|-----------|---------|
| **FastAPI** | High-performance REST API framework |
| **Uvicorn** | ASGI web server |
| **Pydantic** | Data validation & serialization |

#### Data Sources & External APIs
| Source | Data | Frequency |
|--------|------|-----------|
| **CoinGecko** | Crypto prices, market cap | Hourly/Real-time |
| **Binance WebSocket** | BTC/ETH streaming ticks | Live (5s intervals) |
| **Frankfurter API** | Forex rates (EUR, GBP, JPY) | Daily |
| **Finnhub** | Financial news + sentiment | Daily |
| **YFinance** | Metals (Gold, Silver) | Daily |

### Frontend - React Ecosystem

| Technology | Purpose |
|-----------|---------|
| **Vite** | Fast build tool, dev server |
| **React 18** | UI component framework |
| **TypeScript** | Type-safe JavaScript |
| **TailwindCSS** | Utility-first styling |
| **shadcn/ui** | Pre-built accessible components |
| **React Query** | Server state management |
| **Vitest** | Unit testing framework |

### Infrastructure & Deployment

| Component | Role |
|-----------|------|
| **Docker Compose** | Containerization, local orchestration |
| **PostgreSQL 15** | Airflow metadata store |
| **Zookeeper** | Kafka coordination |
| **MinIO** (optional) | S3-compatible object storage |

---

## Architecture Deep Dive

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   DATA INGESTION LAYER                       │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ CoinGecko│  │ Binance  │  │Frankfurt │  │ Finnhub  │   │
│  │  API     │  │ WebSocket│  │   API    │  │   News   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │              │         │
│       └─────────────┼──────────────┴──────────────┘         │
│                     │ Batch & Streaming                     │
└─────────────────────┼─────────────────────────────────────┘
                      │
┌─────────────────────┼─────────────────────────────────────┐
│    KAFKA MESSAGE BUS (Real-time Event Stream)              │
│    Topics: market_stream, news_stream                      │
└─────────────────────┼─────────────────────────────────────┘
                      │
┌─────────────────────┼─────────────────────────────────────┐
│          APACHE AIRFLOW ORCHESTRATION                       │
│    ┌────────────────────────────────────────────────┐      │
│    │  DAG: market_batch_pipeline                    │      │
│    │  - Ingest & validate data                      │      │
│    │  - Transform through layers                    │      │
│    │  - Build features                              │      │
│    │  - Train/predict ML models                     │      │
│    └────────────────────────────────────────────────┘      │
└─────────────────────┼─────────────────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
┌───────▼────────┐        ┌─────────▼──────────┐
│  LAKEHOUSE     │        │   FEATURE STORE    │
│  (Parquet)     │        │   (Gold Layer)     │
│                │        │                    │
│ ┌──────────┐   │        │ ┌──────────────┐   │
│ │ Bronze   │   │        │ │ Indicators   │   │
│ │ (Raw)    │   │        │ │ Sentiments   │   │
│ └──────┬───┘   │        │ │ Correlations │   │
│        │       │        │ │ ML Features  │   │
│ ┌──────▼───┐   │        │ └──────────────┘   │
│ │ Silver   │   │        │                    │
│ │(Cleaned) │   │        │                    │
│ └──────┬───┘   │        │                    │
│        │       │        │                    │
│ ┌──────▼───┐   │        │                    │
│ │ Gold     │   │        │                    │
│ │(Ready)   │   │        │                    │
│ └──────────┘   │        │                    │
└────────────────┘        └────────────────────┘
        │                           │
        └──────────────┬────────────┘
                       │
        ┌──────────────┴───────────────┐
        │                              │
┌───────▼──────────┐          ┌────────▼─────────┐
│   MACHINE        │          │     FASTAPI      │
│   LEARNING       │          │     REST API     │
│                  │          │                  │
│ ┌──────────────┐ │          │ ┌──────────────┐ │
│ │ BTC Direction│ │          │ │ /api/markets │ │
│ │ Prediction   │ │          │ │ /api/news    │ │
│ │              │ │          │ │ /api/predict │ │
│ │ Models:      │ │          │ │ /api/signals │ │
│ │ - Logistic   │ │          │ │ /api/pipeline│ │
│ │ - RF         │ │          │ └──────────────┘ │
│ │ - XGBoost    │ │          │                  │
│ └──────────────┘ │          │   CORS Enabled   │
│                  │          │                  │
│ Metrics:        │          │ Port: 8000       │
│ - Accuracy      │          │                  │
│ - Precision/    │          │                  │
│   Recall        │          │                  │
└──────────┬───────┘          └────────┬──────────┘
           │                          │
           └──────────────┬───────────┘
                          │
                ┌─────────▼──────────┐
                │   REACT FRONTEND   │
                │   (Vite + TailwindCSS)
                │                    │
                │ ┌────────────────┐ │
                │ │ Market Charts  │ │
                │ │ Predictions    │ │
                │ │ News Feed      │ │
                │ │ Signal Panel   │ │
                │ │ Correlations   │ │
                │ └────────────────┘ │
                │                    │
                │  Port: 5173        │
                └────────────────────┘
```

### Data Lakehouse Layers

#### Layer 1: Bronze (Raw) 📥
**Purpose:** Immutable historical record of ingested data

- **Structure:** Organized by source and asset class
  - `bronze/crypto_prices/` → Raw Binance/CoinGecko ticks
  - `bronze/forex_rates/` → Raw FX prices
  - `bronze/metals_prices/` → Raw precious metals
  - `bronze/news/` → Raw news articles + sentiment

- **Format:** Parquet (columnar, compressed)
- **Deduplication:** By timestamp + symbol
- **Retention:** Historical (append-only)

#### Layer 2: Silver (Cleaned) 🧹
**Purpose:** Standardized, validated, business-ready data

- **Transformations:**
  - Handle nulls → forward fill, drop invalid rows
  - Standardize timestamps → UTC
  - Normalize prices → consistent decimal places
  - Remove duplicates → by (symbol, timestamp)
  - Type casting → enforce schemas
  
- **Quality Checks:**
  - Symbol validation
  - Price range checks (outlier detection)
  - Volume > 0 validation
  - Timestamp ordering

- **Modules:**
  - `clean_market_silver.py` → Crypto/Forex/Metals
  - `clean_news_silver.py` → News articles
  - `news_sentiment_silver.py` → Sentiment labels

#### Layer 3: Gold (Features & Analytics) ⚡
**Purpose:** ML-ready features and business metrics

- **Market Features (12 Technical Indicators):**
  - **Core (7):**
    1. `returns` - Daily % change
    2. `price_diff` - Absolute price change
    3. `ma7` - 7-day moving average
    4. `ma30` - 30-day moving average
    5. `volatility` - 20-day rolling std dev
    6. `volume_change` - Volume difference
    7. `correlation` - Symbol vs BTC correlation

  - **Advanced (5):**
    8. `rsi` - Relative Strength Index (0-100)
    9. `macd` - MACD line + signal + histogram
    10. `day_of_week` - Temporal patterns (0-6)
    11. `volume_ma7` - 7-day volume MA
    12. `relative_volume` - Volume vs average ratio

- **News Features:**
  - `sentiment_score` (FinBERT) - Bullish/bearish
  - `sentiment_label` - categorical
  - `news_aggregates` - Daily aggregations

- **Composite Datasets:**
  - `market_features/` → BTC/ETH/FX/Metals with indicators
  - `ml_dataset/` → Features + targets for training
  - `correlation_matrix/` → Cross-asset correlations

### Data Flow Example (BTC/USD)

```
1. INGESTION (Hourly)
   CoinGecko API → timestamp, open, high, low, close, volume, market_cap
   
2. BRONZE
   Parquet: /bronze/crypto_prices/BTC_USD_2026-04-15.parquet
   Record: {timestamp: "2026-04-15T12:00:00Z", close: 67890, volume: 1200000}
   
3. SILVER (Clean)
   - Remove duplicates by (symbol, timestamp)
   - Fill NaN close prices
   - Drop rows with close ≤ 0 or volume = 0
   - Standardize to UTC
   Parquet: /silver/market_data/BTC_USD_2026-04-15.parquet
   
4. GOLD (Features)
   - Calculate returns: (close[t] - close[t-1]) / close[t-1]
   - Calculate ma7: rolling(close, 7).mean()
   - Calculate volatility: rolling(returns, 20).std()
   - Calculate RSI, MACD, etc.
   
   Result: {
     timestamp, symbol, close, volume,
     returns, price_diff, ma7, ma30, volatility,
     rsi, macd, macd_signal, macd_histogram,
     volume_ma7, relative_volume, correlation_btc,
     day_of_week
   }
   
5. ML FEATURE ENGINEERING
   - Select only past information (no lookahead bias)
   - Derive: ma7_ratio = close / ma7
   - Derive: momentum_3d = returns.rolling(3).sum()
   - Drop NaN rows
   
   ML Features: [
     close, volume, returns, price_diff, ma7, ma30,
     volatility, rsi, macd, volume_change,
     ma7_ratio, ma30_ratio, momentum_3d, 
     momentum_7d, volatility_change, ...
   ]
   
6. ML PREDICTION
   Target: 1 if close[t+1] > close[t], else 0
   Train: Walk-forward on 200-day rolling window
   Models tested: Logistic Regression, Random Forest, XGBoost
   
7. API RESPONSE
   Signal: "BUY" (prob_up = 0.72) | "HOLD" | "SELL"
   Metadata: model_type, accuracy, timestamp
```

---

## Backend Architecture Deep Dive

### 1. Configuration Layer (`app/config/`)

#### `settings.py` - Central Configuration Hub

**Environment Management:**
```python
- Load .env files (repo-root, backend-specific)
- Define API base URLs (CoinGecko, Finnhub, Frankfurter)
- Configure Kafka bootstrap servers
- Set data directories (Bronze/Silver/Gold paths)
```

**Key Settings:**
- `PROJECT_ROOT` → repo root for shared data
- `BACKEND_ROOT` → backend directory (Parquet destination)
- `LAKEHOUSE_DIR` → parquet storage root
- `KAFKA_BOOTSTRAP_SERVERS` → localhost:9092 (Docker Compose)
- `STREAM_POLL_INTERVAL_SECONDS` → 5s polling for ticks
- `DEFAULT_REQUEST_TIMEOUT_SECONDS` → 30s API timeout

**Assets Configuration:**
- Crypto pairs: BTC/USD, ETH/USD
- Forex: EUR/USD, GBP/USD, JPY/USD
- Metals: XAU/USD, XAG/USD

#### `logging_config.py` - Structured Logging
```python
- JSON logger for production readiness
- Per-module loggers with context injection
- Both file and console handlers
```

### 2. Ingestion Layer (`app/ingestion/`)

#### Batch Ingestion (`batch/`)

**Base Architecture:**
```python
class BaseIngestor:
    - retry_with_backoff() → exponential backoff on 429/5xx
    - parse_response() → normalize API schemas
    - write_to_bronze() → append-only Parquet
```

**Specific Ingestors:**

| Ingestor | Source | Logic |
|----------|--------|-------|
| `CoinGeckoIngestor` | CoinGecko API | Fetch OHLCV for BTC/ETH; hourly polling with caching |
| `FrankfurterIngestor` | Frankfurter API | Daily EUR/GBP/JPY vs USD rates |
| `MetalsCSVIngestor` | Local CSV seeds | Load XAU_USD.csv, XAG_USD.csv from data/seeds/metals |
| `FinnhubNewsIngestor` | Finnhub API | Fetch crypto/finance news articles daily |
| `YFinanceIngestion` | YFinance | Alternative metals ingestion via yfinance package |

**Flow:**
```
API Call → Parse Response → Normalize Schema → Write Bronze Parquet
```

#### Streaming Ingestion (`streaming/`)

**Kafka Producer Pattern:**
```python
BinanceWSProducer (binance_ws_producer.py):
  - WebSocket connection to Binance stream
  - @aggTrade endpoint → trade ticks every 100ms
  - Emit: {timestamp, symbol, price, quantity} → Kafka market_stream topic
  - Automatic reconnection on disconnect
  
FinnhubNewsWSProducer (finnhub_news_ws_producer.py):
  - WebSocket to Finnhub news stream
  - Emit news → Kafka news_stream topic
  - Include: headline, summary, sentiment placeholders
  
YFinanceMetalsProducer (yfinance_metals_producer.py):
  - Periodic polling of YFinance metals data
  - Emit gold/silver prices to Kafka
```

**Kafka Consumer Patterns:**
```python
KafkaConsumer (kafka_consumer.py):
  - Subscribe to market_stream topic
  - Deserialize JSON messages
  - Accumulate into 5-minute micro-batches
  - Write to Bronze streaming partition
  - Read latest per symbol for real-time ticks
  
NewsKafkaConsumer (news_kafka_consumer.py):
  - Subscribe to news_stream topic
  - Deserialize news JSON messages
  - Batch process and append to Bronze news partition
```

### 3. Lakehouse Layer (`app/etl/`)

#### Bronze Layer (`bronze/`)

**Schema Enforcement:**
```python
class BronzeSchema:
  - symbol: string (BTC/USD, ETH/USD, etc.)
  - timestamp: datetime
  - open, high, low, close, volume: float
  - source: string (coingecko, binance, finnhub, etc.)
  - ingestion_time: datetime (when recorded)
```

**Write Pattern:**
```python
def write_bronze(df):
  - Partition by date: bronze/crypto_prices/2026-04-15/
  - Append mode (no overwrites)
  - Deduplicate by (symbol, timestamp) on read
  - Compression: snappy
```

#### Silver Layer (`silver/`)

**Modules:**
- `clean_market_silver.py` → Unified market data orchestrator (delegates to specific cleaners)
- `clean_crypto_silver.py` → Cryptocurrency price data cleaning and deduplication
- `clean_forex_silver.py` → FX rate data cleaning and standardization
- `clean_metals_silver.py` → Precious metals (gold/silver) cleaning
- `clean_news_silver.py` → News articles with validation and deduplication
- `news_sentiment_silver.py` → FinBERT sentiment scoring and labeling
- `schema_silver.py` → Pydantic schemas for validation

**Quality Rules:**
```python
Rules enforced:
  - price > 0
  - volume ≥ 0
  - timestamp in UTC
  - No future dates
  - Symbol in approved list
  - Max 1 record per symbol per hour (dedup)
```

#### Gold Layer (`gold/`)

**Modules:**
- `build_gold_market.py` → Market features (indicators)
- `build_gold_news.py` → News sentiment aggregates
- `build_gold_sentiment.py` → Daily sentiment scores

**Features Built:**
```python
Technical Indicators:
  - Moving Averages: ma7, ma30
  - Momentum: RSI, MACD
  - Volatility: std(returns, 20)
  - Volume Patterns: rolling averages, relative volume
  - Correlations: symbol vs BTC
```

### 4. Feature Engineering (`app/features/`)

**Two-Phase Feature Building:**

**Phase 1: Simple Features** (`simple_features.py`)
```python
From raw OHLCV:
  1. returns = pct_change(close)
  2. price_diff = close - close.shift()
  3. ma7, ma30 = rolling_mean(close, window)
  4. volatility = rolling_std(returns, 20)
  5. volume_change = volume - volume.shift()
  6. correlation_btc = returns.corr(btc_returns)
```

**Phase 2: Advanced Features** (`advanced_features.py`, if exists)
```python
Derived from Phase 1:
  1. rsi = 100 - (100 / (1 + rs)) where rs = avg_gain / avg_loss
  2. macd = ema12 - ema26, signal = ema(macd, 9)
  3. day_of_week = timestamp.weekday
  4. volume_ma7 = rolling_mean(volume, 7)
  5. relative_volume = volume / volume_ma7
```

**No Lookahead Bias:**
```python
✓ CORRECT:  ma7[t] uses close[t-6:t]
✗ WRONG:    ma7[t] uses close[t:t+6] (future leakage!)
```

### 5. Machine Learning (`app/ml/direction/`)

#### Dataset Loading (`dataset.py`)

```python
load_btc_dataset():
  1. Read gold/market_features/data.parquet
  2. Filter display_symbol == "BTC/USD"
  3. Sort by timestamp ascending
  4. Return DataFrame with all features

build_direction_target(df):
  1. Compute future_return = close[t+1] / close[t] - 1
  2. Binary target = (future_return > 0).astype(int)
  3. Drop last row (no future label)
  4. Return df with 'target' column
```

**Data Example:**
```
timestamp             close   returns   ma7    target
2026-01-01T00:00:00   50000   0.01      49900  1  (went up next day)
2026-01-02T00:00:00   50500   0.01      50100  0  (went down)
2026-01-03T00:00:00   50450  -0.001     50200  1  (went up)
...
```

#### Feature Engineering (`features.py`)

**Build Features:**
```python
build_features(df):
  1. ma7_ratio = close / ma7
  2. ma30_ratio = close / ma30
  3. momentum_3d = returns.rolling(3).sum()
  4. momentum_7d = returns.rolling(7).sum()
  5. volatility_change = volatility.diff()
  6. Drop rows with NaN in engineered features
```

**Select Features:**
```python
select_feature_columns(df):
  1. Exclude: timestamp, symbol, target, future_return, etc.
  2. Include: All numeric columns (close, ma7, rsi, macd, etc.)
  3. Returns: List of column names for X matrix
```

#### Model Training (`trainer.py`)

**Training Pipeline:**
```
1. Load BTC dataset (all history)
   ↓
2. Build targets (binary direction labels)
   ↓
3. Engineer features (ratios, momentum, volatility change)
   ↓
4. Run walk-forward backtest for each model candidate:
   - Logistic Regression
   - Random Forest (400 trees, depth=5)
   - XGBoost (300 trees, lr=0.04, depth=4)
   ↓
5. Select best model by accuracy
   ↓
6. Retrain best model on FULL dataset
   ↓
7. Save to artifacts/:
   - btc_direction_model.pkl (joblib)
   - btc_model_metadata.json (metrics)
```

**Walk-Forward Backtest Logic:**
```python
For i = train_window to total_samples:
  X_train = X[i-200:i]      # Previous 200 days
  y_train = y[i-200:i]
  X_test = X[i:i+1]         # Next day
  y_test = y[i]
  
  model.fit(X_train, y_train)
  prob_up = model.predict_proba(X_test)[0][1]
  pred = 1 if prob_up >= 0.5 else 0
  
  Compare pred to y_test → collect metrics
```

**Output Metrics:**
```python
{
  "model_type": "random_forest",
  "accuracy": 0.5412,
  "precision_up": 0.5089,
  "recall_up": 0.6234,
  "f1": 0.5594,
  "features_used": [...]
}
```

#### Model Prediction (`predictor.py`)

**Prediction Pipeline:**
```
1. Load latest BTC data from gold layer
2. Build target, engineer features
3. Load trained model from artifacts/btc_direction_model.pkl
4. Get latest row
5. Predict probability_up = model.predict_proba(latest)[0][1]
6. Generate signal:
   - prob_up ≥ 0.60 → "BUY"
   - prob_up ≤ 0.40 → "SELL"
   - else → "HOLD"
7. Return JSON response
```

**Output:**
```json
{
  "symbol": "BTC/USD",
  "prediction_date": "2026-04-15T12:00:00Z",
  "signal": "BUY",
  "probability_up": 0.7234,
  "model_type": "random_forest",
  "walk_forward_accuracy": 0.5412
}
```

### 6. Orchestration (`app/orchestration/`)

#### Airflow DAG (`dags/dag_batch_pipeline.py`)

**Scheduling:**
```python
dag_id = "market_batch_pipeline"
schedule_interval = "@hourly"  # Runs every hour
start_date = datetime(2026, 4, 15)
catchup = False  # Don't backfill past runs
```

**Tasks (BashOperators):**
```
1. run_batch_ingestion
   └─→ Executes app.ingestion.batch.run_batch_ingestion
       - CoinGecko, Frankfurter, Metals CSV, Finnhub APIs
       - Writes all sources to Bronze Parquet

2. clean_market_silver
   └─→ Executes app.etl.silver.clean_market_silver
       - Deduplicates by (symbol, timestamp)
       - Validates price ranges, volumes
       - Fills NaNs and standardizes to UTC
       - Outputs to Silver market_data/

3. clean_news_silver
   └─→ Executes app.etl.silver.clean_news_silver
       - Validates news articles
       - Removes duplicates
       - Outputs to Silver news_data/

4. build_gold_market
   └─→ Executes app.etl.gold.build_gold_market
       - Calculates 12 technical indicators
       - Builds correlation features
       - Outputs to Gold market_features/

5. build_gold_news
   └─→ Executes app.etl.gold.build_gold_news
       - Aggregates news sentiment
       - Creates daily news summaries
       - Outputs to Gold news_aggregates/
```

**DAG Flow:**
```
run_batch_ingestion ──┬─→ clean_market_silver ──→ build_gold_market
                      └─→ clean_news_silver ──→ build_gold_news
```

### 7. API Layer (`app/api/`)

#### FastAPI Server (`main.py`)

**Configuration:**
```python
- CORS enabled (allow_origins=["*"])
- Title: "Market Analytics Terminal API"
- Version: 0.1.0
- Docs: http://localhost:8000/docs
```

**Routers (7 total):**
| Route | Module | Purpose |
|-------|--------|----------|
| `/api/markets` | `routes/markets.py` | Asset list, OHLCV history, stream ticks, WebSocket |
| `/api/news` | `routes/news.py` | Latest news articles + sentiment scores |
| `/api/pipeline` | `routes/pipeline.py` | Ingestion/ETL pipeline status and logs |
| `/api/predictions` | `routes/predictions.py` | BTC direction predictions with probabilities |
| `/api/signals` | `routes/signals.py` | Trading signals (BUY/SELL/HOLD) + confidence |
| `/api/correlation` | `routes/correlation.py` | Cross-asset correlation matrix |
| `/api/articles` | `routes/article_reader.py` | Full news article content retrieval |

**Health Check:**
```
GET /healthz → {"status": "ok"}
```

**Port:** 8000 (uvicorn ASGI server)

---

## Frontend Architecture

### Tech Stack
- **Framework:** React 18 with TypeScript
- **Build:** Vite (lightning-fast HMR)
- **Styling:** TailwindCSS + shadcn/ui components
- **State:** React Query (TanStack Query)
- **Testing:** Vitest

### Key Pages (10 Pages)
1. **Index** - Main dashboard landing page
2. **Portfolio** - Asset allocation and holdings view
3. **Streaming** - Real-time price charts and ticks via WebSocket
4. **Predictions** - BTC direction forecasts with confidence intervals
5. **News** - Latest market news with FinBERT sentiment scores
6. **Signals** - Trading signals (BUY/SELL/HOLD) with historical accuracy
7. **History** - Past predictions and backtesting results
8. **Pipeline** - ETL pipeline status, DAG runs, ingestion logs
9. **Correlations** - Cross-asset correlation heatmap and analysis
10. **Alerts** - Custom price alerts and signal notifications

### API Integration
```typescript
// services/api.ts
const api = axios.create({
  baseURL: "http://localhost:8000/api",
  timeout: 5000,
});

// Endpoints consumed:
GET /markets           // Latest prices
GET /predictions       // Current BTC signal
GET /news             // Recent news
GET /signals/:period   // Signal history
```

---

## How It All Works - Example Flow

### Scenario: Hourly Market Pipeline Execution

**Every Hour - Airflow triggers DAG (market_batch_pipeline)**

```
Step 1: INGESTION (~5 mins)
├─ Fetch latest OHLCV from CoinGecko (BTC/ETH) → append to Bronze
├─ Fetch current EUR/USD, GBP/USD, JPY/USD from Frankfurter → append to Bronze
├─ Load XAU_USD, XAG_USD from local CSV seeds → append to Bronze
├─ Fetch latest news articles from Finnhub → append to Bronze
└─ Total: All ingested data written to Bronze layer (Parquet)

Step 2: SILVER CLEANING (~10 mins)
├─ clean_market_silver.py:
│  ├─ Deduplicates by (symbol, timestamp)
│  ├─ Fills NaN prices (forward fill)
│  ├─ Validates: 0 < price ≤ max_expected, volume ≥ 0
│  ├─ Standardizes to UTC
│  └─ Outputs to silver/market_data/
├─ clean_news_silver.py:
│  ├─ Validates article structure
│  ├─ Removes duplicates by headline
│  └─ Outputs to silver/news_data/
└─ All quality checks passed

Step 3: GOLD FEATURE ENGINEERING (~8 mins)
├─ build_gold_market.py:
│  ├─ For each symbol, compute 12 indicators:
│  │  ├─ returns, price_diff, ma7, ma30
│  │  ├─ volatility, rsi, macd, macd_signal
│  │  ├─ volume_ma7, relative_volume, correlation_btc
│  │  └─ day_of_week
│  └─ Outputs to gold/market_features/
├─ build_gold_news.py:
│  ├─ Aggregates daily news by symbol
│  ├─ Applies FinBERT sentiment analysis
│  └─ Outputs to gold/news_aggregates/
└─ All features ready for ML

Step 4: API SERVES UPDATED DATA
├─ GET /api/markets → Latest assets with 12 indicators
├─ GET /api/news → Latest articles with sentiment
├─ GET /api/correlation → Updated correlation matrix
├─ WebSocket → Real-time streaming ticks from Kafka
└─ Frontend refreshes automatically

Step 5: ML TRAINING (Optional, if scheduled)
├─ train_direction_model.py (if enabled):
│  ├─ Load full BTC dataset from Gold
│  ├─ Run walk-forward backtest (200-day window)
│  ├─ Evaluate 3 model types: Logistic, RF, XGBoost
│  ├─ Select best model and retrain on full history
│  └─ Save to ml/direction/artifacts/
└─ Updated predictions available

Step 6: REAL-TIME STREAMING (Parallel, Continuous)
├─ Binance WebSocket → BTC/ETH ticks every 100ms
├─ Kafka producer emits to market_stream topic
├─ Kafka consumer batches → 5-min aggregates
├─ Append to Bronze streaming partition
├─ Frontend WebSocket subscribers receive live updates
└─ No wait for batch pipeline

Step 7: TOTAL TIME: ~20-30 mins (hourly execution)
```

---

## Deployment Model

### Local Development (`docker-compose.yml`)

**Services Spun Up:**

```yaml
Services:
  1. Zookeeper → Kafka coordinator (port 2181)
  2. Kafka → Message broker (port 9092)
  3. PostgreSQL → Airflow metadata store (port 5433)
  4. Airflow Init → DB migration + user creation
  5. Airflow Webserver → DAG UI (port 8080)
  6. Airflow Scheduler → Runs DAGs on schedule
  7. Backend API → FastAPI (port 8000)
  8. Frontend → Vite dev server (port 5173)

Volumes:
  - ./backend/app/orchestration/dags → /opt/airflow/dags
  - ./backend/logs → /opt/airflow/logs
  - ./backend → /opt/airflow/project
  - ./data → /opt/airflow/data (seeds)
  - airflow_postgres_data → persistent DB

Environment:
  - AIRFLOW__CORE__EXECUTOR: LocalExecutor
  - PYTHONPATH: /opt/airflow/project
  - KAFKA_BOOTSTRAP_SERVERS: localhost:9092
```

**Start Command:**
```bash
docker-compose up --build
```

**Access:**
- Airflow UI: http://localhost:8080 (admin/admin)
- Backend API: http://localhost:8000/docs
- Frontend: http://localhost:5173

### Production Readiness Checklist

- [ ] Use managed services (Airflow on Cloud Composer, Kafka on MSK)
- [ ] Add authentication/authorization (OAuth2, API keys)
- [ ] Implement monitoring (Prometheus, Datadog)
- [ ] Add alerting (PagerDuty, Slack)
- [ ] Implement retry logic (exponential backoff)
- [ ] Set up data validation (Great Expectations)
- [ ] Add SLA monitoring
- [ ] Implement model monitoring (prediction drift, data drift)
- [ ] Secure secrets (Vault, AWS Secrets Manager)
- [ ] Set up CI/CD (GitHub Actions, GitLab CI)

---

## Key Achievements

✅ **Multi-source Data Integration** - Crypto, Forex, Metals, News  
✅ **Real-time Streaming** - Kafka producers/consumers for live ticks  
✅ **Modern Lakehouse Architecture** - Bronze/Silver/Gold layering  
✅ **Feature-rich ML** - 12 technical indicators, 3 model types  
✅ **Walk-forward Backtesting** - Realistic ML evaluation  
✅ **Trading Signals** - BUY/SELL/HOLD with confidence scores  
✅ **REST API** - FastAPI with CORS, async support  
✅ **Modern Frontend** - React with real-time updates  
✅ **Orchestration** - Airflow DAGs for reproducible pipelines  
✅ **Docker Containerization** - Easy local/cloud deployment  

---

## Summary

**Crypto-Dashboard** demonstrates enterprise data engineering patterns:

1. **Scalable ingestion** across multiple APIs
2. **Reliable transformation** through quality-gated layers
3. **Advanced analytics** with technical indicators
4. **Predictive ML** with rigorous backtesting
5. **Production-grade APIs** for consumption
6. **Modern frontend** for visualization
7. **Containerized deployment** for reproducibility

Perfect for learning or productionizing financial data pipelines!
