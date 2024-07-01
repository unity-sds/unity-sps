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

with DAG(
    dag_id="env_test",
    default_args=default_args,
    schedule=None,
    is_paused_upon_creation=False,
    tags=["test"],
) as dag:
    dump_env = BashOperator(
        task_id="env",
        bash_command="env",
    )

    check_vars = BashOperator(
        task_id="check",
        bash_command="echo {} {} {} {} {}".format(
            Variable.get("unity_project"),
            Variable.get("unity_venue"),
            Variable.get("unity_deployment_name"),
            Variable.get("unity_counter"),
            Variable.get("unity_cluster_name"),
        ),
    )
    dump_env >> check_vars
