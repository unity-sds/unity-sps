import os
import subprocess
import shutil
from datetime import datetime
from urllib.parse import urlparse
from glob import glob

from kubernetes.client import models as k8s

from airflow import DAG
from airflow.decorators import task
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator, get_current_context
from airflow.operators.bash_operator import BashOperator
from airflow.models.param import Param


default_args = {"owner": "unity-sps", "start_date": datetime.utcfromtimestamp(0)}


with DAG(
    dag_id="vic2png",
    default_args=default_args,
    schedule=None,
    tags=["vic2png"],
    params={
        "vic_url": Param(
            "s3://unity-gmanipon-ads-deployment-dev/output/SAM_0000_0734432789_658ECMNAUT_040960LUJ01.VIC",
            type="string",
        ),
        "output_url": Param(
            "s3://unity-gmanipon-ads-deployment-dev/output", type="string"
        ),
    },
) as dag:

    @task
    def prep(params: dict):
        context = get_current_context()
        dag_run_id = context["dag_run"].run_id
        original_umask = os.umask(0)
        vic2png_args = {}
        try:
            dag_run_dir = f"/shared-task-data/{dag_run_id}"
            if os.path.isdir(dag_run_dir):
                shutil.rmtree(dag_run_dir)
            os.mkdir(dag_run_dir)
            print(f"dag_run_dir: {dag_run_dir}")
            for i in ["stage-in", "stage-out"]:
                dag_run_subdir = os.path.join(dag_run_dir, i)
                os.mkdir(dag_run_subdir)
                print(f"dag_run_subdir: {dag_run_subdir}")
                if i == "stage-in":
                    s3_hook = S3Hook()
                    for k, v in params.items():
                        if k == "output_url":
                            continue
                        parsed_url = urlparse(v)
                        s3_hook.download_file(
                            bucket_name=parsed_url.netloc,
                            key=parsed_url.path[1:],
                            local_path=dag_run_subdir,
                            preserve_file_name=True,
                            use_autogenerated_subdir=False,
                        )
                        vic2png_args[k] = os.path.join(
                            f"/{i}", os.path.basename(parsed_url.path)
                        )
                res = subprocess.run(
                    ["ls", "-l", dag_run_subdir], capture_output=True, text=True
                )
                print(res.stdout)
                print(res.stderr)
        finally:
            os.umask(original_umask)
        cli_args = [
            vic2png_args["vic_url"],
            "--out",
            "/stage-out",
        ]
        res = subprocess.run(["find", dag_run_dir], capture_output=True, text=True)
        print(res.stdout)
        print(res.stderr)
        print(f"cli_args: {cli_args}")
        return cli_args

    prep_task = prep()

    vic2png_task = KubernetesPodOperator(
        task_id="vic2png",
        name="vic2png",
        namespace="sps",
        image="pymonger/srl-idps-vic2png:develop",
        # cmds=[
        #   "sh",
        #   "-c",
        #   "ls -l /stage-in/*;ls -l /stage-out;mkdir -p /airflow/xcom/;echo '[1,2,3,4]' > /airflow/xcom/return.json",
        # ],
        arguments=prep_task,
        do_xcom_push=True,
        on_finish_action="delete_pod",
        in_cluster=False,
        get_logs=True,
        container_logs=True,
        # service_account_name="airflow-worker",
        # container_security_context={"privileged": True},
        volume_mounts=[
            k8s.V1VolumeMount(
                name="workers-volume",
                mount_path="/stage-in",
                sub_path="{{ dag_run.run_id }}/stage-in",
            ),
            k8s.V1VolumeMount(
                name="workers-volume",
                mount_path="/stage-out",
                sub_path="{{ dag_run.run_id }}/stage-out",
            ),
        ],
        volumes=[
            k8s.V1Volume(
                name="workers-volume",
                persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(
                    claim_name="airflow-kpo"
                ),
            )
        ],
    )

    @task
    def post(params: dict):
        context = get_current_context()
        dag_run_id = context["dag_run"].run_id
        dag_run_dir = f"/shared-task-data/{dag_run_id}"
        stage_out_dir = os.path.join(dag_run_dir, "stage-out")
        print(f"stage_out_dir: {stage_out_dir}")
        s3_hook = S3Hook()
        bucket, prefix = s3_hook.parse_s3_url(params["output_url"])
        output_urls = []
        for i in glob(os.path.join(stage_out_dir, "*.png")):
            dest_key = os.path.join(prefix, os.path.basename(i))
            s3_hook.load_file(
                bucket_name=bucket, key=dest_key, filename=i, replace=True
            )
            print(f"Copying {i} to {dest_key}.")
            output_urls.append(f"s3://{bucket}/{dest_key}")
        return output_urls

    post_task = post()

    prep_task >> vic2png_task >> post_task
