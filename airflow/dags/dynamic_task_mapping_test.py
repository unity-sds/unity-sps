import os
import re
import subprocess
from datetime import datetime
from urllib.parse import urlparse

from airflow.decorators import task
from airflow.exceptions import AirflowFailException
from airflow.models.param import Param
from airflow.operators.python import PythonOperator, ShortCircuitOperator, get_current_context
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.utils.trigger_rule import TriggerRule
from kubernetes.client import models as k8s

from airflow import DAG

default_args = {"owner": "unity-sps", "start_date": datetime.utcfromtimestamp(0)}

with DAG(
    dag_id="dynamic_task_mapping_test",
    default_args=default_args,
    schedule=None,
    tags=["dynamic_task_mapping_test"],
    params={"start_index": Param(0, type="integer"), "end_index": Param(9, type="integer")},
) as dag:

    @task
    def enumerate_list(params: dict):
        context = get_current_context()
        dag_run_id = context["dag_run"].run_id
        start = params["start_index"]
        end = params["end_index"]
        ret_list = []
        for i in range(start, end):
            ret_list.append(
                {
                    "trigger_dag_id": "test_sum" if i % 2 == 0 else "test_sum2",
                    "conf": {"first_val": i, "second_val": i},
                }
            )
        return ret_list

    enumerate_list_task = enumerate_list()

    trigger_sum_task = TriggerDagRunOperator.partial(
        task_id="trigger_sum",
        reset_dag_run=True,
        map_index_template="{{ task.trigger_run_id }}",
        wait_for_completion=False,
        trigger_rule=TriggerRule.ALL_SUCCESS,
    ).expand_kwargs(enumerate_list_task)

    enumerate_list_task >> trigger_sum_task
