"""
# DAG Name: Env Test

# Purpose

# Usage
"""  # noqa: E501

from datetime import datetime

from airflow.models import Variable
from airflow.operators.bash import BashOperator

from airflow import DAG

default_args = {
    "owner": "unity-sps",
    "start_date": datetime.utcfromtimestamp(0),
}


dump_env = BashOperator(
    task_id="env",
    bash_command="env",
)

check_vars = BashOperator(
    task_id="check",
    bash_command=format(
        "echo %s %s %s %s %s",
        Variable.get("unity_project"),
        Variable.get("venue"),
        Variable.get("deployment_name"),
        Variable.get("counter"),
        Variable.get("cluster_name"),
    ),
)


dag = DAG(
    dag_id="env_test",
    default_args=default_args,
    schedule=None,
    is_paused_upon_creation=False,
    tags=["test"],
)

dump_env > check_vars
