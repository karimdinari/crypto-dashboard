from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

from app.orchestration.airflow_config import DEFAULT_DAG_ARGS


with DAG(
    dag_id="market_batch_pipeline",
    default_args=DEFAULT_DAG_ARGS,
    description="Batch pipeline for Bronze -> Silver -> Gold",
    schedule_interval="@daily",
    start_date=datetime(2026, 4, 15) ,
    catchup=False,
    tags=["market", "batch", "lakehouse"],
) as dag:

    run_batch_ingestion = BashOperator(
        task_id="run_batch_ingestion",
        bash_command="cd /opt/airflow/project && python -m app.ingestion.batch.run_batch_ingestion",
    )

    clean_market_silver = BashOperator(
        task_id="clean_market_silver",
        bash_command="cd /opt/airflow/project && python -m app.etl.silver.clean_market_silver",
    )

    clean_news_silver = BashOperator(
        task_id="clean_news_silver",
        bash_command="cd /opt/airflow/project && python -m app.etl.silver.clean_news_silver",
    )

    build_gold_market = BashOperator(
        task_id="build_gold_market",
        bash_command="cd /opt/airflow/project && python -m app.etl.gold.build_gold_market",
    )

    build_gold_news = BashOperator(
        task_id="build_gold_news",
        bash_command="cd /opt/airflow/project && python -m app.etl.gold.build_gold_news",
    )

    run_batch_ingestion >> [clean_market_silver, clean_news_silver]
    clean_market_silver >> build_gold_market
    clean_news_silver >> build_gold_news