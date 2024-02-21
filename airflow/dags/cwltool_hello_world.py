from datetime import datetime

from airflow.operators.bash import BashOperator

from airflow import DAG

default_args = {
    "owner": "unity-sps",
    "start_date": datetime.utcfromtimestamp(0),
}

dag = DAG(
    "cwltool_help_dag",
    default_args=default_args,
    description="A simple DAG to run cwltool --help",
    schedule=None,
    is_paused_upon_creation=False,
    tags=["test"],
)

run_cwl_help = BashOperator(
    task_id="run_cwltool_help",
    bash_command="cwltool --help",
    dag=dag,
)

run_cwl_help
