import os
import re
from datetime import datetime

from airflow.decorators import task
from airflow.exceptions import AirflowFailException
from airflow.models.param import Param
from airflow.operators.python import get_current_context
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.utils.trigger_rule import TriggerRule

from airflow import DAG

default_args = {"owner": "unity-sps", "start_date": datetime.utcfromtimestamp(0)}

FNAME_RE = re.compile(
    r"^(?P<id>(?P<instrument>SA|SB|FL|FR)(?P<color>[A-GJ-MORTX-Z_])(?P<specFlag>[A-Z_])(?P<primaryTime>\d{4})(?P<spacer0>[A-Z_])(?P<secondaryTime>\d{10})(?P<spacer1>_)(?P<tertiaryTime>\d{3})(?P<prodType>[A-Z_]{3})(?P<geometry>[NT])(?P<seqId>[A-Z]{3}[A-Z_]\d{5})(?P<downsample>[0-3_])(?P<compression>[A-Z0-9]{2})(?P<producer>[A-Z_])(?P<version>[A-Z0-9_]{2}))(?P<extension>\.VIC)$"
)


with DAG(
    dag_id="eval_srl_vic2png",
    default_args=default_args,
    schedule=None,
    tags=["eval_srl_vic2png"],
    params={
        "payload": Param(
            "s3://unity-gmanipon-ads-deployment-dev/output/SAM_0000_0734432789_658ECMNAUT_040960LUJ01.VIC",
            type="string",
        )
    },
) as dag:

    @task(weight_rule="absolute", priority_weight=112)
    def evaluate_vic2png(params: dict):
        s3_hook = S3Hook()

        # parse triggering payload
        payload = params["payload"]
        bucket, key = s3_hook.parse_s3_url(payload)
        fname = os.path.basename(key)

        # ensure matches filename convention and parse filename components
        match = FNAME_RE.search(fname)
        if not match:
            raise AirflowFailException("Filename {fname} not recognized.")

        # build expected file prefixes (TODO: fix hardcoding)
        keys = {"vic": (bucket, key)}

        # default vic2png DAG parameters
        vic2png_args = {"success": True, "vic_url": None, "id": match.groupdict()["id"]}

        # check if all inputs exist
        for k, v in keys.items():
            exists = s3_hook.check_for_key(v[1], bucket_name=v[0])
            vic2png_args["success"] &= exists
            if exists:
                vic2png_args[f"{k}_url"] = f"s3://{v[0]}/{v[1]}"

        # return params and evaluation result
        return vic2png_args

    evaluate_vic2png_task = evaluate_vic2png()

    @task.short_circuit(weight_rule="absolute", priority_weight=113)
    def vic2png_evaluation_successful():
        context = get_current_context()
        print(f"{context['ti'].xcom_pull(task_ids='evaluate_vic2png')}")
        return context["ti"].xcom_pull(task_ids="evaluate_vic2png")["success"]

    vic2png_evaluation_successful_task = vic2png_evaluation_successful()

    trigger_vic2png_task = TriggerDagRunOperator(
        weight_rule="absolute",
        priority_weight=114,
        task_id="trigger_vic2png",
        trigger_dag_id="vic2png",
        # uncomment the next line if we want to dedup dagRuns for a particular ID
        trigger_run_id="{{ ti.xcom_pull(task_ids='evaluate_vic2png')['id'] }}-vic2png",
        trigger_rule=TriggerRule.ALL_SUCCESS,
        skip_when_already_exists=True,
        conf={
            "vic_url": "{{ ti.xcom_pull(task_ids='evaluate_vic2png')['vic_url'] }}",
            "output_url": "s3://gmanipon-dev-sps-isl/STACAM/PNG",
        },
    )

    evaluate_vic2png_task >> vic2png_evaluation_successful_task >> trigger_vic2png_task
