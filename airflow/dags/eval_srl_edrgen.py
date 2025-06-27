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
    r"^(?P<id>(?P<apid>\d{4})_(?P<sclk_seconds>\d{10})-(?P<sclk_subseconds>\d{5})-(?P<version>\d{1,3}))\.(?P<ext>\w{3})$"
)


with DAG(
    dag_id="eval_srl_edrgen",
    default_args=default_args,
    schedule=None,
    tags=["eval_srl_edrgen"],
    params={
        "payload": Param(
            "s3://unity-gmanipon-ads-deployment-dev/srl/edrgen/inputs/0980_0734432789-43133-1.dat",
            type="string",
        )
    },
) as dag:

    @task(weight_rule="absolute", priority_weight=100)
    def evaluate_edrgen(params: dict):
        s3_hook = S3Hook()

        # parse triggering payload
        payload = params["payload"]
        bucket, key = s3_hook.parse_s3_url(payload)
        fname = os.path.basename(key)
        path = os.path.dirname(key)

        # ensure matches filename convention and parse filename components
        match = FNAME_RE.search(fname)
        if not match:
            raise AirflowFailException("Filename {fname} not recognized.")

        # build expected file prefixes (TODO: fix hardcoding)
        keys = {}
        if match.groupdict()["ext"] == "dat":
            keys["dat"] = (bucket, key)
            keys["emd"] = (bucket, f"{path}/{match.groupdict()['id']}.emd")
        elif match.groupdict()["ext"] == "emd":
            keys["emd"] = (bucket, key)
            keys["dat"] = (bucket, f"{path}/{match.groupdict()['id']}.dat")
        else:
            raise AirflowFailException(f"Extension {match.groupdict()['ext']} not recognized.")
        keys["fsw"] = (
            "unity-gmanipon-ads-deployment-dev",
            f"srl/edrgen/static/srl/current/products/dp_{match.groupdict()['apid'][1:]}_v0.xml",
        )

        # default edrgen DAG parameters
        edrgen_args = {
            "success": True,
            "dat_url": None,
            "emd_url": None,
            "fsw_url": None,
            "id": match.groupdict()["id"],
        }

        # check if all inputs exist
        for k, v in keys.items():
            exists = s3_hook.check_for_key(v[1], bucket_name=v[0])
            edrgen_args["success"] &= exists
            if exists:
                edrgen_args[f"{k}_url"] = f"s3://{v[0]}/{v[1]}"

        # return params and evaluation result
        return edrgen_args

    evaluate_edrgen_task = evaluate_edrgen()

    @task.short_circuit()
    def edrgen_evaluation_successful():
        context = get_current_context()
        print(f"{context['ti'].xcom_pull(task_ids='evaluate_edrgen')}")
        return context["ti"].xcom_pull(task_ids="evaluate_edrgen")["success"]

    edrgen_evaluation_successful_task = edrgen_evaluation_successful()

    trigger_edrgen_task = TriggerDagRunOperator(
        weight_rule="absolute",
        priority_weight=102,
        task_id="trigger_edrgen",
        trigger_dag_id="edrgen",
        # uncomment the next line if we want to dedup dagRuns for a particular ID
        trigger_run_id="{{ ti.xcom_pull(task_ids='evaluate_edrgen')['id'] }}",
        trigger_rule=TriggerRule.ALL_SUCCESS,
        skip_when_already_exists=True,
        conf={
            "dat_url": "{{ ti.xcom_pull(task_ids='evaluate_edrgen')['dat_url'] }}",
            "emd_url": "{{ ti.xcom_pull(task_ids='evaluate_edrgen')['emd_url'] }}",
            "fsw_url": "{{ ti.xcom_pull(task_ids='evaluate_edrgen')['fsw_url'] }}",
            "output_url": "s3://gmanipon-dev-sps-isl/STACAM/VIC",
        },
    )

    evaluate_edrgen_task >> edrgen_evaluation_successful_task >> trigger_edrgen_task
