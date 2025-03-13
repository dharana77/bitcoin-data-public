from airflow import DAG
from airflow.operators.http_operator import SimpleHttpOperator
from datetime import datetime, timedelta

# DAG 기본 설정
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 2, 2),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# DAG 생성
dag = DAG(
    "fetch_crypto_data",
    default_args=default_args,
    description="Fetch data from crypto API and send to Kafka",
    schedule_interval=timedelta(minutes=5),  # 5분마다 실행
)

# FastAPI 호출
fetch_data_task = SimpleHttpOperator(
    task_id="fetch_data",
    method="GET",
    http_conn_id="crypto_api",
    endpoint="/fetch-data",
    dag=dag,
)