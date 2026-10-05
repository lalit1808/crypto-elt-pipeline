import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow/extract_load")

from airflow import DAG
from airflow.operators.python import PythonOperator

from crypto_pipeline import ensure_tables, get_tracked_coins, extract_normalize_load_historical

default_args = {
    "owner": "lalit",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def run_historical_load():
    ensure_tables()
    coin_ids = get_tracked_coins()
    extract_normalize_load_historical(coin_ids)


with DAG(
    dag_id="crypto_historical_dag",
    default_args=default_args,
    schedule_interval=None,
    start_date=datetime(2026, 9, 1),
    catchup=False,
    tags=["crypto", "historical", "manual-backfill"],
) as dag:

    historical_task = PythonOperator(
        task_id="extract_normalize_load_historical",
        python_callable=run_historical_load,
    )