from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 2, 2),
    "retries": 1,
    "retry_delay": timedelta(minutes=15),
}

dag = DAG(
    "silver_to_gold",
    default_args=default_args,
    description="Transform Silver data to Gold",
    schedule_interval=timedelta(minutes=15),  # 15분마다 실행
)

transform_task = BashOperator(
    task_id="run_gold_transform",
    bash_command="python gold_transform.py",
    dag=dag,
)
