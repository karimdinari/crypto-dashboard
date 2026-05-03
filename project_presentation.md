# Crypto Dashboard Project Presentation

## Overview
The Crypto Dashboard project is a comprehensive data engineering and analytics platform designed to process, analyze, and visualize cryptocurrency and financial market data. It integrates multiple technologies and follows a modular architecture to ensure scalability, maintainability, and efficiency.

---

## Project Architecture
The project is divided into two main components:

1. **Backend**: Handles data ingestion, processing, storage, and API services.
2. **Frontend**: Provides a user-friendly interface for data visualization and interaction.

---

## Backend Pipeline

### 1. **Ingestion and Streaming** (Expanded)
- **Real-Time Data Collection**:
  - **Goal**: Capture live updates from cryptocurrency markets and financial data providers.
  - **How It Works**:
    - **Binance WebSocket** streams real-time cryptocurrency prices.
    - **Kafka** acts as a message broker, ensuring reliable delivery of streaming data.
    - Data is ingested into the Bronze layer for raw storage.
  - **Configuration**:
    - WebSocket URLs and Kafka topics are defined in `backend/app/config/settings.py`.

- **Batch Data Collection**:
  - **Goal**: Periodically fetch historical or aggregated data.
  - **How It Works**:
    - APIs like CoinGecko and Frankfurter provide batch data.
    - Python scripts in `backend/app/ingestion/batch/` handle scheduled data pulls.
    - Data is stored in the Bronze layer for further processing.
  - **Configuration**:
    - API keys and endpoints are managed in `.env` files.

### 2. **Storage and Transformation** (Expanded)
- **Bronze Layer**:
  - **Goal**: Store raw, unprocessed data as-is.
  - **How It Works**:
    - Data from ingestion pipelines is saved in Parquet format.
    - Acts as the single source of truth for raw data.

- **Silver Layer**:
  - **Goal**: Clean and structure data for analysis.
  - **How It Works**:
    - Data cleaning scripts in `backend/app/etl/silver/` remove duplicates and handle missing values.
    - Data is normalized and structured into tables.

- **Gold Layer**:
  - **Goal**: Provide aggregated and feature-engineered data for analytics and machine learning.
  - **How It Works**:
    - Feature engineering scripts in `backend/app/features/` create derived metrics.
    - Aggregated data is stored in Parquet files for efficient querying.

### 3. **Machine Learning and Features**
- **Goal**: Generate predictions and insights.
- **Technologies Used**:
  - **Python**: ML models and feature engineering scripts in `backend/app/ml/` and `backend/app/features/`.
  - **Libraries**: Scikit-learn, Pandas, NumPy.
- **Configuration**:
  - ML models are loaded and served using `backend/app/serving/`.

### 4. **Orchestration** (Expanded)
- **Goal**: Automate and manage the execution of data pipelines.
- **How It Works**:
  - **Airflow DAGs**:
    - Directed Acyclic Graphs (DAGs) define the sequence of tasks.
    - Tasks include ingestion, transformation, and loading into layers.
  - **Scheduler**:
    - Airflow schedules tasks based on defined intervals (e.g., hourly, daily).
    - Ensures dependencies between tasks are respected.
  - **Monitoring**:
    - Logs and dashboards in Airflow provide visibility into pipeline execution.

- **Configuration**:
  - DAGs are defined in `backend/app/orchestration/dags/`.
  - Airflow settings are managed in `infra/docker/airflow/`.
  - Environment variables control task parameters and schedules.

### 5. **API Services**
- **Goal**: Expose data and insights to the frontend.
- **Technologies Used**:
  - **FastAPI**: RESTful API framework.
  - **CORS Middleware**: Enables cross-origin requests.
- **Configuration**:
  - API routes are defined in `backend/app/api/routes/`.
  - The main entry point is `backend/app/api/main.py`.

---

## Frontend

### 1. **User Interface**
- **Goal**: Provide an interactive dashboard for users.
- **Technologies Used**:
  - **React**: Frontend framework.
  - **Vite**: Build tool for fast development.
  - **Tailwind CSS**: Styling framework.
- **Configuration**:
  - Vite configuration is in `frontend/vite.config.ts`.
  - Components and pages are in `frontend/src/`.

### 2. **Data Visualization**
- **Goal**: Display processed data and insights.
- **Technologies Used**:
  - **Chart.js**: For rendering charts.
  - **React Query**: For data fetching and state management.
- **Configuration**:
  - API endpoints are consumed from the backend.

---

## Key Learnings
1. **Data Engineering**:
   - Implementing a lakehouse architecture.
   - Managing real-time and batch data pipelines.
2. **Backend Development**:
   - Building scalable APIs with FastAPI.
   - Configuring and using Kafka for streaming.
3. **Frontend Development**:
   - Creating responsive and interactive dashboards with React and Tailwind CSS.
   - Integrating frontend with backend APIs.
4. **Orchestration**:
   - Automating workflows with Airflow.

---

## Conclusion
The Crypto Dashboard project demonstrates the integration of modern data engineering practices with full-stack development. It provides a robust platform for analyzing and visualizing financial data, showcasing the team's ability to work with diverse technologies and solve complex problems.