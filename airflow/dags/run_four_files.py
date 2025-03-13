from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# 기본 인수 설정
default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
    # 필요 시 재시도, 알림 등 추가 설정 가능
}

# DAG 정의 (매일 실행하는 예시)
with DAG(
    'run_four_python_files',
    default_args=default_args,
    description='세 개의 파이썬 파일을 순차적으로 실행하는 DAG',
    schedule_interval="*/15 * * * *",  # 15분마다 실행
    catchup=False,
) as dag:

    run_bronze = BashOperator(
        task_id='run_bronze',
        # 파일 경로는 서버 내에서의 절대경로나 상대경로를 사용 (예: /home/airflow/myproject/file1.py)
        bash_command='python bronze/raw_data2.py',
        cwd='/root/bitcoin-data/'
    )

    run_silver = BashOperator(
        task_id='run_silver',
        bash_command='python silver/feature_extraction.py',
        cwd='/root/bitcoin-data/'
    )

    run_gold = BashOperator(
        task_id='run_gold',
        bash_command='python gold/combine_data.py',
        cwd='/root/bitcoin-data/'
    )

    run_analysis = BashOperator(
        task_id="run_analysis",
        bash_command="python model/analysis/load_and_analysis3.py",
        cwd='/root/bitcoin-data/'
    )

    # 순차 실행: file1 → file2 → file3
    run_bronze >> run_silver >> run_gold >> run_analysis
