import os
import re
import subprocess
from datetime import datetime
from urllib.parse import urlparse

from kubernetes.client import models as k8s

from airflow import DAG
from airflow.decorators import task
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.trigger_rule import TriggerRule
from airflow.operators.python import PythonOperator, get_current_context, ShortCircuitOperator
from airflow.models.param import Param
from airflow.exceptions import AirflowFailException
from airflow.providers.amazon.aws.hooks.s3 import S3Hook


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
        return [{"conf": {"first_val": i, "second_val": i}} for i in range(start, end)]

    enumerate_list_task = enumerate_list()

    trigger_sum_task = TriggerDagRunOperator.partial(
        task_id="trigger_sum",
        trigger_dag_id="test_sum",
        reset_dag_run=True,
        map_index_template="{{ task.trigger_run_id }}",
        wait_for_completion=False,
        trigger_rule=TriggerRule.ALL_SUCCESS,
    ).expand_kwargs(enumerate_list_task)

    enumerate_list_task >> trigger_sum_task
