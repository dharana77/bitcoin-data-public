from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 2, 2),
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

dag = DAG(
    "bronze_to_silver",
    default_args=default_args,
    description="Transform Bronze data to Silver",
    schedule_interval=timedelta(minutes=10),  # 10분마다 실행
)

transform_task = BashOperator(
    task_id="run_spark_transform",
    bash_command="python silver_transform.py",
    dag=dag,
)