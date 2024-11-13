"""
DAG to execute a generic CWL workflow.

The Airflow KubernetesPodOperator starts a Docker container that includes the Docker engine and the CWL libraries.
The "cwl-runner" tool is invoked to execute the CWL workflow.
Parameter cwl_workflow: the URL of the CWL workflow to execute.
Parameter args_as_json: JSON string contained the specific values for the workflow specific inputs.
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
import requests
import yaml

from airflow import DAG

# Task constants
UNITY_STAGE_IN_WORKFLOW = "https://raw.githubusercontent.com/unity-sds/unity-data-services/refs/heads/cwl-examples/cwl/stage-in-unity/stage-in-workflow.cwl"
DAAC_STAGE_IN_WORKFLOW = "https://raw.githubusercontent.com/unity-sds/unity-data-services/refs/heads/cwl-examples/cwl/stage-in-daac/stage-in-workflow.cwl"
LOCAL_DIR = "/shared-task-data"
DOWNLOAD_DIR = "input"

# The path of the working directory where the CWL workflow is executed
# (aka the starting directory for cwl-runner).
# This is fixed to the EFS /scratch directory in this DAG.
WORKING_DIR = "/scratch"

# Default parameters
DEFAULT_CWL_WORKFLOW = (
    "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/main/demos/echo_message.cwl"
)
DEFAULT_CWL_ARGUMENTS = json.dumps({"message": "Hello Unity"})
DEFAULT_STAC_JSON_URL = "https://cmr.earthdata.nasa.gov/stac/LPCLOUD/collections/EMITL1BRAD_001/items?limit=2"
DEFAULT_INPUT_LOCATION = "daac"


# Alternative arguments to execute SBG Pre-Process
# DEFAULT_CWL_WORKFLOW =  "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.cwl"
# DEFAULT_CWL_ARGUMENTS = "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.dev.yml"

# Alternative arguments to execute SBG end-to-end
# DEFAULT_CWL_WORKFLOW =  "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/L1-to-L2-e2e.cwl"
# DEFAULT_CWL_ARGUMENTS = "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/L1-to-L2-e2e.dev.yml"

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
STAGE_IN_CONTAINER_RESOURCES = k8s.V1ResourceRequirements(
    requests={
        "memory": "4Gi",
        "cpu": "4",
        "ephemeral-storage": "{{ params.request_storage }}",
    }
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
        "cwl_workflow": Param(
            DEFAULT_CWL_WORKFLOW, type="string", title="CWL workflow", description="The CWL workflow URL"
        ),
        "cwl_args": Param(
            DEFAULT_CWL_ARGUMENTS,
            type="string",
            title="CWL workflow parameters",
            description=("The job parameters encoded as a JSON string," "or the URL of a JSON or YAML file"),
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
        "stac_json_url": Param(
            DEFAULT_STAC_JSON_URL,
            type="string",
            title="STAC JSON URL",
            description="The URL to the STAC JSON document",
        ),
        "input_location": Param(
            DEFAULT_INPUT_LOCATION,
            type="string",
            enum=["daac", "unity"],
            title="Input data location",
            description="Indicate whether input data should be retrieved from a DAAC or Unity",
        ),
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


def select_stage_in(ti, stac_json_url, input_location):
    """
    Determine stage in workflow and required arguments.
    """
    stage_in_args = {"download_dir": DOWNLOAD_DIR, "stac_json": stac_json_url}
    if input_location == "daac":
        stage_in_workflow = DAAC_STAGE_IN_WORKFLOW
    else:
        stage_in_workflow = UNITY_STAGE_IN_WORKFLOW
        ssm_client = boto3.client("ssm", region_name="us-west-2")
        ss_acct_num = ssm_client.get_parameter(Name=unity_sps_utils.SS_ACT_NUM, WithDecryption=True)[
            "Parameter"
        ]["Value"]
        unity_client_id = ssm_client.get_parameter(
            Name=f"arn:aws:ssm:us-west-2:{ss_acct_num}:parameter{unity_sps_utils.DS_CLIENT_ID_PARAM}",
            WithDecryption=True,
        )["Parameter"]["Value"]
        stage_in_args["unity_client_id"] = unity_client_id

    ti.xcom_push(key="stage_in_workflow", value=stage_in_workflow)
    logging.info("Stage In workflow selected: %s", stage_in_workflow)

    ti.xcom_push(key="stage_in_args", value=stage_in_args)
    logging.info("Stage in arguments selected: %s", stage_in_args)


def select_process(ti, dag_run_id, cwl_args):
    """
    Determine process task CWL arguments.
    """
    input_dir = f"{WORKING_DIR}/{DOWNLOAD_DIR}"
    if cwl_args.endswith("yml") or cwl_args.endswith("yaml"):
        yaml_data = requests.get(cwl_args, headers={"User-Agent":"SPS/Airflow"}).text
        json_data = yaml.safe_load(yaml_data)
    else:
        json_data = json.loads(cwl_args)
    json_data["input"] = {
        "class": "Directory",
        "path": input_dir
    }
    ti.xcom_push(key="cwl_args", value=json.dumps(json_data))
    logging.info("Modified CWL args for processing task.")


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

    # define stage in arguments
    select_stage_in(
        ti,
        context["params"]["stac_json_url"],
        context["params"]["input_location"],
    )

    # define process arguments
    select_process(ti, dag_run_id, context["params"]["cwl_args"])


setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)


cwl_task_stage_in = unity_sps_utils.SpsKubernetesPodOperator(
    retries=0,
    task_id="cwl_task_stage_in",
    namespace=unity_sps_utils.POD_NAMESPACE,
    name="cwl-task-pod",
    image=unity_sps_utils.SPS_DOCKER_CWL_IMAGE,
    service_account_name="airflow-worker",
    in_cluster=True,
    get_logs=True,
    startup_timeout_seconds=1800,
    arguments=[
        "-w",
        "{{ ti.xcom_pull(task_ids='Setup', key='stage_in_workflow') }}",
        "-j",
        "{{ ti.xcom_pull(task_ids='Setup', key='stage_in_args') }}",
        "-e",
        "{{ ti.xcom_pull(task_ids='Setup', key='ecr_login') }}",
    ],
    container_security_context={"privileged": True},
    container_resources=STAGE_IN_CONTAINER_RESOURCES,
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
    node_selector={"karpenter.sh/nodepool": unity_sps_utils.NODE_POOL_DEFAULT},
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


cwl_task_processing = unity_sps_utils.SpsKubernetesPodOperator(
    retries=0,
    task_id="cwl_task_processing",
    namespace=unity_sps_utils.POD_NAMESPACE,
    name="cwl-task-pod",
    image=unity_sps_utils.SPS_DOCKER_CWL_IMAGE,
    service_account_name="airflow-worker",
    in_cluster=True,
    get_logs=True,
    startup_timeout_seconds=1800,
    arguments=[
        "-w",
        "{{ params.cwl_workflow }}",
        "-j",
        "{{ ti.xcom_pull(task_ids='Setup', key='cwl_args') }}",
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

chain(
    setup_task.as_setup(), cwl_task_stage_in, cwl_task_processing, cleanup_task.as_teardown(setups=setup_task)
)
