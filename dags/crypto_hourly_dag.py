import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow/extract_load")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from crypto_pipeline import (
    ensure_tables,
    get_tracked_coins,
    backfill_new_coins,
    get_all_known_coin_ids,
    extract_normalize_load_daily,
    send_slack_alert,
)


def alert_on_failure(context):
    task_id = context["task_instance"].task_id
    dag_id = context["task_instance"].dag_id
    execution_date = context["execution_date"]
    send_slack_alert(
        f":red_circle: Airflow task failed\n"
        f"DAG: {dag_id}\n"
        f"Task: {task_id}\n"
        f"Time: {execution_date}"
    )


default_args = {
    "owner": "lalit",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": alert_on_failure,
}


def run_hourly_snapshot():
    ensure_tables()
    top25_today = get_tracked_coins()
    backfill_new_coins(top25_today)
    all_known = get_all_known_coin_ids()
    extract_normalize_load_daily(all_known)


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

    dbt_freshness_task = BashOperator(
        task_id="dbt_source_freshness",
        bash_command="cd /opt/airflow/dbt_project && dbt source freshness --profiles-dir .",
    )

    extract_task >> dbt_run_task >> dbt_test_task >> dbt_freshness_task