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

ROUTER_CFG = [
    {
        "regex": "(?<=/)(?P<apid>0980|0990)_(?P<sclk_seconds>\d{10})-(?P<sclk_subseconds>\d{5})-(?P<version>\d{1,3})(?P<extension>\.dat|\.emd)$",
        "evaluators": ["eval_srl_edrgen"],
    },
    {
        "regex": "(?<=/)(?P<instrument>SA|SB|FL|FR)(?P<color>[A-GJ-MORTX-Z_])(?P<specFlag>[A-Z_])(?P<primaryTime>\d{4})(?P<spacer0>[A-Z_])(?P<secondaryTime>\d{10})(?P<spacer1>_)(?P<tertiaryTime>\d{3})(?P<prodType>[A-Z_]{3})(?P<geometry>[NT])(?P<seqId>[A-Z]{3}[A-Z_]\d{5})(?P<downsample>[0-3_])(?P<compression>[A-Z0-9]{2})(?P<producer>[A-Z_])(?P<version>[A-Z0-9_]{2})(?P<extension>\.VIC)$",
        "evaluators": ["eval_srl_vic2png", "eval_srl_rdrgen"],
    },
]

default_args = {"owner": "unity-sps", "start_date": datetime.utcfromtimestamp(0)}

with DAG(
    dag_id="router",
    default_args=default_args,
    schedule=None,
    tags=["router"],
    params={
        "payload": Param(
            "s3://unity-gmanipon-ads-deployment-dev/srl/edrgen/inputs/0980_0734432789-43133-1.dat",
            type="string",
        )
    },
) as dag:

    @task
    def enumerate_evaluators(params: dict):
        context = get_current_context()
        dag_run_id = context["dag_run"].run_id
        payload = params["payload"]
        evaluators = []
        for route_cfg in ROUTER_CFG:
            regex = re.compile(route_cfg["regex"])
            match = regex.search(payload)
            if match:
                for evaluator_name in route_cfg["evaluators"]:
                    evaluators.append({"trigger_dag_id": evaluator_name, "conf": {"payload": payload}})
        return evaluators

    enumerate_evals_task = enumerate_evaluators()

    trigger_eval_task = TriggerDagRunOperator.partial(
        task_id="route_payload_to_evaluator", wait_for_completion=False, trigger_rule=TriggerRule.ALL_SUCCESS
    ).expand_kwargs(enumerate_evals_task)

    enumerate_evals_task >> trigger_eval_task
