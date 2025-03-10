from __future__ import annotations

from datetime import datetime

from airflow.decorators import task
from airflow.models.dag import DAG
from airflow.models.param import Param

with DAG(
    dag_id="test_sum",
    schedule=None,
    tags=["test_sum"],
    params={"first_val": Param(0, type="integer"), "second_val": Param(0, type="integer")},
) as dag:

    @task
    def sum_them(params: dict):
        return params["first_val"] + params["second_val"]

    sum_task = sum_them()
