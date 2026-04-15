from datetime import timedelta

DEFAULT_DAG_ARGS = {
    "owner": "market-pipeline-team",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}