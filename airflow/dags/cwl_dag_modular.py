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
STAGE_IN_WORKFLOW = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/307-log-levels/demos/stage_in_log_level.cwl"
STAGE_OUT_WORKFLOW = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/307-log-levels/demos/stage_out_cwl_log_level.cwl"
LOCAL_DIR = "/shared-task-data"

# The path of the working directory where the CWL workflow is executed
# (aka the starting directory for cwl-runner).
# This is fixed to the EFS /scratch directory in this DAG.
WORKING_DIR = "/scratch"

# Default parameters
DEFAULT_STAC_JSON = "https://raw.githubusercontent.com/unity-sds/unity-tutorial-application/refs/heads/main/test/stage_in/stage_in_results.json"
DEFAULT_PROCESS_WORKFLOW = (
    "https://raw.githubusercontent.com/mike-gangl/unity-OGC-example-application/refs/heads/main/process.cwl"
)
DEFAULT_PROCESS_ARGS = json.dumps({"example_argument_empty": ""})
DEFAULT_LOG_LEVEL = 20

CONTAINER_RESOURCES = k8s.V1ResourceRequirements(
    requests={
        "ephemeral-storage": "{{ti.xcom_pull(task_ids='Setup', key='container_storage')}}",
    }
)

EC2_TYPES = {
    "t3.micro": {
        "desc": "General Purpose",
        "cpu": 1,
        "memory": 1,
    },
    "t3.small": {
        "desc": "General Purpose",
        "cpu": 2,
        "memory": 2,
    },
    "t3.medium": {
        "desc": "General Purpose",
        "cpu": 2,
        "memory": 4,
    },
    "t3.large": {
        "desc": "General Purpose",
        "cpu": 2,
        "memory": 8,
    },
    "t3.xlarge": {
        "desc": "General Purpose",
        "cpu": 4,
        "memory": 16,
    },
    "t3.2xlarge": {
        "desc": "General Purpose",
        "cpu": 8,
        "memory": 32,
    },
    "r7i.xlarge": {
        "desc": "Memory Optimized",
        "cpu": 4,
        "memory": 32,
    },
    "r7i.2xlarge": {
        "desc": "Memory Optimized",
        "cpu": 8,
        "memory": 64,
    },
    "r7i.4xlarge": {
        "desc": "Memory Optimized",
        "cpu": 16,
        "memory": 128,
    },
    "r7i.8xlarge": {
        "desc": "Memory Optimized",
        "cpu": 32,
        "memory": 256,
    },
    "c6i.xlarge": {
        "desc": "Compute Optimized",
        "cpu": 4,
        "memory": 8,
    },
    "c6i.2xlarge": {
        "desc": "Compute Optimized",
        "cpu": 8,
        "memory": 16,
    },
    "c6i.4xlarge": {
        "desc": "Compute Optimized",
        "cpu": 16,
        "memory": 32,
    },
    "c6i.8xlarge": {
        "desc": "Compute Optimized",
        "cpu": 32,
        "memory": 64,
    },
}

# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}


# "t3.large": "t3.large (General Purpose: 2vCPU, 8GiB)",
def build_ec2_type_label(key):
    return f"{key} ({EC2_TYPES.get(key)['desc']}: {EC2_TYPES.get(key)['cpu']}vCPU, {EC2_TYPES.get(key)['memory']}GiB)"


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
        "log_level": Param(
            DEFAULT_LOG_LEVEL,
            type="string",
            enum=["20", "10", "30", "40", "50"],
            title="Stage in/out log level",
            description=("Default log level for stage in and stage out tasks"),
        ),
        "request_instance_type": Param(
            "t3.medium",
            type="string",
            enum=list(EC2_TYPES.keys()),
            values_display={key: f"{build_ec2_type_label(key)}" for key in EC2_TYPES.keys()},
            title="EC2 instance type",
        ),
        "request_storage": Param(
            "10Gi", type="string", enum=["10Gi", "50Gi", "100Gi", "150Gi", "200Gi", "250Gi"]
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


def select_node_pool(ti, request_storage, request_instance_type):
    """
    Select node pool based on resources requested in input parameters.
    """
    node_pool = unity_sps_utils.NODE_POOL_DEFAULT
    storage = int(request_storage[0:-2])  # 100Gi -> 100
    ti.xcom_push(key="container_storage", value=storage)
    logging.info(f"Selecting container storage={storage}")

    # from "t3.large (General Purpose: 2vCPU, 8GiB)" to "t3.large"
    cpu = EC2_TYPES[request_instance_type]["cpu"]
    memory = EC2_TYPES[request_instance_type]["memory"]
    ti.xcom_push(key="instance_type", value=request_instance_type)
    logging.info(f"Requesting EC2 instance type={request_instance_type}")

    logging.info(f"Requesting storage={storage}Gi memory={memory}Gi CPU={cpu}")
    if (storage > 30) or (memory > 32) or (cpu > 8):
        node_pool = unity_sps_utils.NODE_POOL_HIGH_WORKLOAD
    ti.xcom_push(key="node_pool", value=node_pool)
    logging.info(f"Selecting node pool={node_pool}")


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

    project = os.environ["AIRFLOW_VAR_UNITY_PROJECT"]
    venue = os.environ["AIRFLOW_VAR_UNITY_VENUE"]
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
    select_node_pool(ti, context["params"]["request_storage"], context["params"]["request_instance_type"])

    # select "use_ecr" argument and determine if ECR login is required
    select_ecr(ti, context["params"]["use_ecr"])

    # retrieve stage out aws api key and account id
    select_stage_out(ti)

    logging.info(f"Selected log level: {context['params']['log_level']}")


setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)


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
    cmds=["/usr/share/cwl/docker_cwl_entrypoint_modular.sh"],
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
        "-l",
        "{{ params.log_level }}",
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
    node_selector={
        "karpenter.sh/nodepool": "{{ti.xcom_pull(task_ids='Setup', key='node_pool')}}",
        "node.kubernetes.io/instance-type": "{{ti.xcom_pull(task_ids='Setup', key='instance_type')}}",
    },
    labels={"pod": unity_sps_utils.POD_LABEL},
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
