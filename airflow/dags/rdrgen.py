import os
import shutil
import subprocess
from datetime import datetime
from glob import glob
from urllib.parse import urlparse

import unity_sps_utils
from airflow.decorators import task
from airflow.models.param import Param
from airflow.operators.python import get_current_context
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s

from airflow import DAG

default_args = {"owner": "unity-sps", "start_date": datetime.utcfromtimestamp(0)}


with DAG(
    dag_id="rdrgen",
    default_args=default_args,
    schedule=None,
    tags=["rdrgen"],
    params={
        "vic_url": Param(
            "s3://unity-gmanipon-ads-deployment-dev/output/SAM_0000_0734432789_658ECMNAUT_040960LUJ01.VIC",
            type="string",
        ),
        "output_url": Param("s3://unity-gmanipon-ads-deployment-dev/output", type="string"),
    },
) as dag:

    @task(weight_rule="absolute", priority_weight=109)
    def prep(params: dict):
        context = get_current_context()
        dag_run_id = context["dag_run"].run_id
        original_umask = os.umask(0)
        rdrgen = {}
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
                        rdrgen[k] = os.path.join(f"/{i}", os.path.basename(parsed_url.path))
                res = subprocess.run(["ls", "-l", dag_run_subdir], capture_output=True, text=True)
                print(res.stdout)
                print(res.stderr)
        finally:
            os.umask(original_umask)

        # KLUDGE: The “product id” is typically the only thing that changes in the filename
        # between rdr generation programs, it’s a three letter code in the middle
        # of the filename (in your case “ECM” is the product id). The meaning of
        # product ID codes and which ones should be used with what pipeline process
        # is typically defined in the SIS, but we haven’t defined it on this mission
        # yet. For your case, you would string replace “ECM” with “EDR” for the output
        # from marsinverter.
        output_vic_file = os.path.join(
            "/stage-out", os.path.basename(rdrgen["vic_url"]).replace("ECM", "EDR")
        )

        # cli_args = ["-c", f"select d && exec $MARSLIB/marsinverter {rdrgen['vic_url']} {output_vic_file}"]
        # KLUDGE: ignore non-zero exit code when no-op occurs
        # cli_args = ["-c", f"select d && $MARSLIB/marsinverter {rdrgen['vic_url']} {output_vic_file} || :"]
        cli_args = [
            "-c",
            f"export LD_LIBRARY_PATH=/usr/local/vicar/external/xerces-c++/v3.0.0_rhel8/x86-64-linx/lib:/usr/local/vicar/dev/olb/x86-64-linx:/usr/local/vicar/external/embree/v3.7.0/x86-64-linx; /usr/local/vicar/dev/mars/lib/x86-64-linx/marsinverter {rdrgen['vic_url']} {output_vic_file} || :",
        ]
        res = subprocess.run(["find", dag_run_dir], capture_output=True, text=True)
        print(res.stdout)
        print(res.stderr)
        print(f"cli_args: {cli_args}")
        return cli_args

    prep_task = prep()

    rdrgen = KubernetesPodOperator(
        weight_rule="absolute",
        priority_weight=110,
        task_id="rdrgen",
        name="rdrgen",
        namespace="sps",
        image="429178552491.dkr.ecr.us-west-2.amazonaws.com/srl-idps/rdrgen:develop-multiarch",
        # image="pymonger/srl-idps-rdrgen:multiarch-test",
        # cmds=["/bin/tcsh"],
        cmds=["/bin/bash"],
        arguments=prep_task,
        do_xcom_push=True,
        on_finish_action="delete_pod",
        in_cluster=True,
        get_logs=True,
        startup_timeout_seconds=1800,
        container_logs=True,
        service_account_name="airflow-worker",
        container_security_context={"privileged": True},
        retries=3,
        volume_mounts=[
            k8s.V1VolumeMount(
                name="workers-volume", mount_path="/stage-in", sub_path="{{ dag_run.run_id }}/stage-in"
            ),
            k8s.V1VolumeMount(
                name="workers-volume", mount_path="/stage-out", sub_path="{{ dag_run.run_id }}/stage-out"
            ),
        ],
        volumes=[
            k8s.V1Volume(
                name="workers-volume",
                persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="airflow-kpo"),
            )
        ],
        node_selector={
            "karpenter.sh/nodepool": unity_sps_utils.NODE_POOL_HIGH_WORKLOAD,
            "node.kubernetes.io/instance-type": "c6i.large",
        },
        labels={"pod": unity_sps_utils.POD_LABEL},
        annotations={"karpenter.sh/do-not-disrupt": "true"},
        affinity=unity_sps_utils.get_affinity(
            capacity_type=["spot"], anti_affinity_label=unity_sps_utils.POD_LABEL
        ),
    )

    @task(weight_rule="absolute", priority_weight=111)
    def post(params: dict):
        context = get_current_context()
        dag_run_id = context["dag_run"].run_id
        dag_run_dir = f"/shared-task-data/{dag_run_id}"
        stage_out_dir = os.path.join(dag_run_dir, "stage-out")
        print(f"stage_out_dir: {stage_out_dir}")
        s3_hook = S3Hook()
        bucket, prefix = s3_hook.parse_s3_url(params["output_url"])
        output_urls = []
        for i in glob(os.path.join(stage_out_dir, "*.VIC")):
            dest_key = os.path.join(prefix, os.path.basename(i))
            s3_hook.load_file(bucket_name=bucket, key=dest_key, filename=i, replace=True)
            print(f"Copying {i} to {dest_key}.")
            output_urls.append(f"s3://{bucket}/{dest_key}")
        return output_urls

    post_task = post()

    prep_task >> rdrgen >> post_task
