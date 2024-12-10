"""
DAG to execute a generic CWL workflow.

The Airflow KubernetesPodOperator starts a Docker container that includes the Docker engine and the CWL libraries.
The "cwl-runner" tool is invoked to execute the CWL workflow.
Parameter stage_in_args: The stage in job parameters encoded as a JSON string
Parameter process_workflow: the URL of the CWL workflow to execute.
Parameter process_args: JSON string contained the specific values for the processing workflow specific inputs.
Parameter stage_out_bucket: The S3 bucket to stage data out to.
Parameter collection_id: The output collection identifier for processed data.
"""

import json
import logging
import os
import pathlib
import shutil
from datetime import datetime

import boto3
import unity_sps_utils
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from airflow.operators.python import PythonOperator, get_current_context
from airflow.utils.trigger_rule import TriggerRule
from kubernetes.client import models as k8s

from airflow import DAG

# Task constants
STAGE_IN_WORKFLOW = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/219-process-task/demos/cwl_dag_stage_in.cwl"
STAGE_OUT_WORKFLOW = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/219-process-task/demos/cwl_dag_stage_out.cwl"
LOCAL_DIR = "/shared-task-data"

# The path of the working directory where the CWL workflow is executed
# (aka the starting directory for cwl-runner).
# This is fixed to the EFS /scratch directory in this DAG.
WORKING_DIR = "/scratch"

# Default parameters
DEFAULT_STAC_JSON = "https://raw.githubusercontent.com/unity-sds/unity-tutorial-application/main/test/stage_in/stage_in_results.json"
DEFAULT_PROCESS_WORKFLOW = (
    "https://raw.githubusercontent.com/mike-gangl/unity-OGC-example-application/refs/heads/main/process.cwl"
)
DEFAULT_PROCESS_ARGS = json.dumps({"example_argument_empty": ""})

# Alternative arguments to execute SBG Pre-Process
# DEFAULT_PROCESS_WORKFLOW =  "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.cwl"
# DEFAULT_PROCESS_ARGS = "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.dev.yml"

# Alternative arguments to execute SBG end-to-end
# DEFAULT_PROCESS_WORKFLOW =  "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/L1-to-L2-e2e.cwl"
# DEFAULT_PROCESS_ARGS = "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/L1-to-L2-e2e.dev.yml"

# Alternative arguments to execute SBG end-to-end
# unity_sps_sbg_debug.txt
CONTAINER_RESOURCES = k8s.V1ResourceRequirements(
    requests={
        # "cpu": "2660m",  # 2.67 vCPUs, specified in milliCPUs
        # "memory": "22Gi",  # Rounded to 22 GiB for easier specification
        "memory": "{{ params.request_memory }}",
        "cpu": "{{ params.request_cpu }} ",
        "ephemeral-storage": "{{ params.request_storage }} ",
    },
    # limits={
    #    # "cpu": "2660m",  # Optional: set the same as requests if you want a fixed allocation
    #    # "memory": "22Gi",
    #    "ephemeral-storage": "30Gi"
    # },
)

# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}


dag = DAG(
    dag_id="cwl_dag_modular",
    description="CWL DAG Modular",
    dag_display_name="CWL DAG Modular",
    tags=["CWL"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=10,
    max_active_tasks=30,
    default_args=dag_default_args,
    params={
        "stac_json": Param(
            DEFAULT_STAC_JSON,
            type="string",
            title="STAC JSON",
            description="STAC JSON data to download granules encoded as a JSON string or the URL of a JSON or YAML file",
        ),
        "process_workflow": Param(
            DEFAULT_PROCESS_WORKFLOW,
            type="string",
            title="Processing workflow",
            description="The processing workflow URL",
        ),
        "process_args": Param(
            DEFAULT_PROCESS_ARGS,
            type="string",
            title="Processing workflow parameters",
            description=(
                "The processing job parameters encoded as a JSON string," "or the URL of a JSON or YAML file"
            ),
        ),
        "request_memory": Param(
            "4Gi",
            type="string",
            enum=["4Gi", "8Gi", "16Gi", "32Gi", "64Gi", "128Gi", "256Gi"],
            title="Docker container memory",
        ),
        "request_cpu": Param(
            "4",
            type="string",
            enum=["2", "4", "8", "16", "32"],
            title="Docker container CPU",
        ),
        "request_storage": Param(
            "10Gi",
            type="string",
            enum=["10Gi", "50Gi", "100Gi", "150Gi", "200Gi", "250Gi"],
            title="Docker container storage",
        ),
        "use_ecr": Param(False, type="boolean", title="Log into AWS Elastic Container Registry (ECR)"),
    },
)


def create_local_dir(dag_run_id):
    """
    Create local directory for working DAG data.
    """
    local_dir = f"{LOCAL_DIR}/{dag_run_id}"
    os.makedirs(local_dir, exist_ok=True)
    logging.info(f"Created directory: {local_dir}")


def select_node_pool(ti, request_storage, request_memory, request_cpu):
    """
    Select node pool based on resources requested in input parameters.
    """
    node_pool = unity_sps_utils.NODE_POOL_DEFAULT
    storage = int(request_storage[0:-2])  # 100Gi -> 100
    memory = int(request_memory[0:-2])  # 32Gi -> 32
    cpu = int(request_cpu)  # 8

    logging.info(f"Requesting storage={storage}Gi memory={memory}Gi CPU={cpu}")
    if (storage > 30) or (memory > 32) or (cpu > 8):
        node_pool = unity_sps_utils.NODE_POOL_HIGH_WORKLOAD
    logging.info(f"Selecting node pool={node_pool}")
    ti.xcom_push(key="node_pool_processing", value=node_pool)


def select_ecr(ti, use_ecr):
    """
    Determine if ECR login is required.
    """
    logging.info("Use ECR: %s", use_ecr)
    if use_ecr:
        ecr_login = os.environ["AIRFLOW_VAR_ECR_URI"]
        ti.xcom_push(key="ecr_login", value=ecr_login)
        logging.info("ECR login: %s", ecr_login)


def select_stage_out(ti):
    """Retrieve stage out input parameters from SSM parameter store."""
    ssm_client = boto3.client("ssm", region_name="us-west-2")

    project = ssm_client.get_parameter(Name=unity_sps_utils.SPS_PROJECT_PARAM, WithDecryption=True)[
        "Parameter"
    ]["Value"]

    venue = ssm_client.get_parameter(Name=unity_sps_utils.SPS_VENUE_PARAM, WithDecryption=True)["Parameter"][
        "Value"
    ]

    staging_bucket = ssm_client.get_parameter(Name=unity_sps_utils.DS_S3_BUCKET_PARAM, WithDecryption=True)[
        "Parameter"
    ]["Value"]

    stage_out_args = json.dumps({"project": project, "venue": venue, "staging_bucket": staging_bucket})
    logging.info(f"Selecting stage out args={stage_out_args}")
    ti.xcom_push(key="stage_out_args", value=stage_out_args)


def setup(ti=None, **context):
    """
    Task that creates the working directory on the shared volume
    and parses the input parameter values.
    """
    context = get_current_context()

    # create local working directory
    dag_run_id = context["dag_run"].run_id
    create_local_dir(dag_run_id)

    # select the node pool based on what resources were requested
    select_node_pool(
        ti,
        context["params"]["request_storage"],
        context["params"]["request_memory"],
        context["params"]["request_cpu"],
    )

    # select "use_ecr" argument and determine if ECR login is required
    select_ecr(ti, context["params"]["use_ecr"])

    # retrieve stage out aws api key and account id
    select_stage_out(ti)


setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)


cwl_task_processing = unity_sps_utils.SpsKubernetesPodOperator(
    retries=0,
    task_id="cwl_task_processing",
    namespace=unity_sps_utils.POD_NAMESPACE,
    name="cwl-task-pod",
    image=unity_sps_utils.SPS_DOCKER_CWL_IMAGE_MODULAR,
    service_account_name="airflow-worker",
    in_cluster=True,
    get_logs=True,
    startup_timeout_seconds=1800,
    arguments=[
        "-i",
        STAGE_IN_WORKFLOW,
        "-s",
        "{{ params.stac_json }}",
        "-w",
        "{{ params.process_workflow }}",
        "-j",
        "{{ params.process_args }}",
        "-o",
        STAGE_OUT_WORKFLOW,
        "-d",
        "{{ ti.xcom_pull(task_ids='Setup', key='stage_out_args') }}",
        "-e",
        "{{ ti.xcom_pull(task_ids='Setup', key='ecr_login') }}",
    ],
    container_security_context={"privileged": True},
    container_resources=CONTAINER_RESOURCES,
    container_logs=True,
    volume_mounts=[
        k8s.V1VolumeMount(name="workers-volume", mount_path=WORKING_DIR, sub_path="{{ dag_run.run_id }}")
    ],
    volumes=[
        k8s.V1Volume(
            name="workers-volume",
            persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="airflow-kpo"),
        )
    ],
    dag=dag,
    node_selector={"karpenter.sh/nodepool": "{{ti.xcom_pull(task_ids='Setup', key='node_pool_processing')}}"},
    labels={"app": unity_sps_utils.POD_LABEL},
    annotations={"karpenter.sh/do-not-disrupt": "true"},
    # note: 'affinity' cannot yet be templated
    affinity=unity_sps_utils.get_affinity(
        capacity_type=["spot"],
        # instance_type=["t3.2xlarge"],
        anti_affinity_label=unity_sps_utils.POD_LABEL,
    ),
    on_finish_action="keep_pod",
    is_delete_operator_pod=False,
)


def cleanup(**context):
    """
    Tasks that deletes all data shared between Tasks
    from the Kubernetes PersistentVolume
    """
    dag_run_id = context["dag_run"].run_id
    local_dir = f"{LOCAL_DIR}/{dag_run_id}"
    if os.path.exists(local_dir):
        dir_list = pathlib.Path(local_dir)
        dir_list = list(dir_list.rglob("*"))
        for dir_item in dir_list:
            logging.info("Directory listing: %s", str(dir_item))
        shutil.rmtree(local_dir)
        logging.info(f"Deleted directory: {local_dir}")
    else:
        logging.info(f"Directory does not exist, no need to delete: {local_dir}")


cleanup_task = PythonOperator(
    task_id="Cleanup", python_callable=cleanup, dag=dag, trigger_rule=TriggerRule.ALL_DONE
)


chain(setup_task.as_setup(), cwl_task_processing, cleanup_task.as_teardown(setups=setup_task))
