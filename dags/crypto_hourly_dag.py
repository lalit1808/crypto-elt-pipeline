import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow/extract_load")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from crypto_pipeline import ensure_tables, get_tracked_coins, backfill_new_coins, extract_normalize_load_daily

default_args = {
    "owner": "lalit",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def run_hourly_snapshot():
    ensure_tables()
    coin_ids = get_tracked_coins()
    backfill_new_coins(coin_ids)
    extract_normalize_load_daily(coin_ids)


with DAG(
    dag_id="crypto_hourly_dag",
    default_args=default_args,
    schedule_interval="@hourly",
    start_date=datetime(2026, 9, 1),
    catchup=False,
    tags=["crypto", "hourly"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_normalize_load_daily",
        python_callable=run_hourly_snapshot,
    )

    dbt_run_task = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt_project && dbt run --profiles-dir .",
    )

    dbt_test_task = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt_project && dbt test --profiles-dir .",
    )

    extract_task >> dbt_run_task >> dbt_test_task