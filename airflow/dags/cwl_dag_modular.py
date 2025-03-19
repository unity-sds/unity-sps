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
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from airflow.operators.python import PythonOperator, get_current_context
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.utils.trigger_rule import TriggerRule
from kubernetes.client import models as k8s
from unity_sps_utils import (
    # CS_SHARED_SERVICES_ACCOUNT_ID,
    # CS_SHARED_SERVICES_ACCOUNT_REGION,
    DEFAULT_LOG_LEVEL,
    # DS_COGNITO_CLIENT_ID,
    # DS_S3_BUCKET_PARAM,
    EC2_TYPES,
    LOG_LEVEL_TYPE,
    NODE_POOL_DEFAULT,
    NODE_POOL_HIGH_WORKLOAD,
    POD_LABEL,
    POD_NAMESPACE,
    # SPS_DOCKER_CWL_IMAGE,
    build_ec2_type_label,
    get_affinity,
)

CS_SHARED_SERVICES_ACCOUNT_ID = "/unity/shared-services/aws/account"
CS_SHARED_SERVICES_ACCOUNT_REGION = "/unity/shared-services/aws/account/region"
DS_COGNITO_CLIENT_ID = "/unity/shared-services/dapa/client-id"
DS_S3_BUCKET_PARAM = f"/unity/unity/{os.environ['AIRFLOW_VAR_UNITY_VENUE']}/ds/datastore-bucket"
SPS_DOCKER_CWL_IMAGE = "ghcr.io/unity-sds/unity-sps/sps-docker-cwl:351-stage-in-unity"

from airflow import DAG

# Task constants
SSM_CLIENT = boto3.client("ssm", region_name="us-west-2")
STAGE_IN_WORKFLOW = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/351-stage-in-unity/demos/cwl_dag_modular_stage_in.cwl"
STAGE_OUT_WORKFLOW = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/307-log-levels/demos/stage_out_cwl_log_level.cwl"
LOCAL_DIR = "/shared-task-data"

# The path of the working directory where the CWL workflow is executed
# (aka the starting directory for cwl-runner).
# This is fixed to the EFS /scratch directory in this DAG.
# WORKING_DIR = "/scratch"

# Default parameters
DEFAULT_STAC_JSON = "https://raw.githubusercontent.com/unity-sds/unity-tutorial-application/refs/heads/main/test/stage_in/stage_in_results.json"
DEFAULT_PROCESS_WORKFLOW = (
    "https://raw.githubusercontent.com/mike-gangl/unity-OGC-example-application/refs/heads/main/process.cwl"
)
DEFAULT_PROCESS_ARGS = json.dumps({"example_argument_empty": ""})

CONTAINER_RESOURCES = k8s.V1ResourceRequirements(
    requests={
        "ephemeral-storage": "{{ti.xcom_pull(task_ids='Setup', key='container_storage')}}",
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
            type="integer",
            enum=list(LOG_LEVEL_TYPE.keys()),
            values_display={key: f"{key} ({value})" for key, value in LOG_LEVEL_TYPE.items()},
            title="Processing log levels",
            description=("Log level for modular DAG processing"),
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
        "unity_stac_auth_type": Param(
            False, type="boolean", title="STAC JSON authentication for Unity hosted files"
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
    node_pool = NODE_POOL_DEFAULT
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
        node_pool = NODE_POOL_HIGH_WORKLOAD
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


def select_stage_in(ti, stac_json, unity_stac_auth_type):
    """Retrieve stage in arguments based on authentication type parameter."""
    stage_in_args = {"stac_json": stac_json, "stac_auth_type": "NONE"}
    if unity_stac_auth_type:
        shared_services_account = SSM_CLIENT.get_parameter(
            Name=CS_SHARED_SERVICES_ACCOUNT_ID, WithDecryption=True
        )["Parameter"]["Value"]
        shared_services_region = SSM_CLIENT.get_parameter(
            Name=CS_SHARED_SERVICES_ACCOUNT_REGION, WithDecryption=True
        )["Parameter"]["Value"]
        unity_client_id = SSM_CLIENT.get_parameter(
            Name=f"arn:aws:ssm:{shared_services_region}:{shared_services_account}:parameter{DS_COGNITO_CLIENT_ID}",
            WithDecryption=True,
        )["Parameter"]["Value"]
        stage_in_args["unity_client_id"] = unity_client_id
        stage_in_args["stac_auth_type"] = "UNITY"

    stage_in_args = json.dumps(stage_in_args)
    logging.info(f"Selecting stage in args={stage_in_args}")
    ti.xcom_push(key="stage_in_args", value=stage_in_args)


def select_stage_out(ti):
    """Retrieve stage out input parameters from SSM parameter store."""
    # project = os.environ["AIRFLOW_VAR_UNITY_PROJECT"]
    project = "unity"
    venue = os.environ["AIRFLOW_VAR_UNITY_VENUE"]
    staging_bucket = SSM_CLIENT.get_parameter(Name=DS_S3_BUCKET_PARAM, WithDecryption=True)["Parameter"][
        "Value"
    ]

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

    # retrieve stage in auth type and arguments
    select_stage_in(ti, context["params"]["stac_json"], context["params"]["unity_stac_auth_type"])

    # retrieve stage out aws api key and account id
    select_stage_out(ti)

    # select log level based on debug
    logging.info(f"Selecting log level: {context['params']['log_level']}.")


setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)


cwl_task_processing = KubernetesPodOperator(
    retries=0,
    task_id="cwl_task_processing",
    namespace=POD_NAMESPACE,
    name="cwl-task-pod",
    image=SPS_DOCKER_CWL_IMAGE,
    service_account_name="airflow-worker",
    in_cluster=True,
    get_logs=True,
    startup_timeout_seconds=1800,
    cmds=["/usr/share/cwl/docker_cwl_entrypoint_modular.sh"],
    arguments=[
        "-i",
        STAGE_IN_WORKFLOW,
        "-s",
        "{{ ti.xcom_pull(task_ids='Setup', key='stage_in_args') }}",
        "-w",
        "{{ params.process_workflow }}",
        "-j",
        "{{ params.process_args }}",
        "-o",
        STAGE_OUT_WORKFLOW,
        "-a",
        "{{ ti.xcom_pull(task_ids='Setup', key='stage_out_args') }}",
        "-l",
        "{{ params.log_level }}",
        "-e",
        "{{ ti.xcom_pull(task_ids='Setup', key='ecr_login') }}",
    ],
    container_security_context={"privileged": True},
    container_resources=CONTAINER_RESOURCES,
    container_logs=True,
    # volume_mounts=[
    #     k8s.V1VolumeMount(name="workers-volume", mount_path=WORKING_DIR, sub_path="{{ dag_run.run_id }}")
    # ],
    # volumes=[
    #     k8s.V1Volume(
    #         name="workers-volume",
    #         persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="airflow-kpo"),
    #     )
    # ],
    dag=dag,
    node_selector={
        "karpenter.sh/nodepool": "{{ti.xcom_pull(task_ids='Setup', key='node_pool')}}",
        "node.kubernetes.io/instance-type": "{{ti.xcom_pull(task_ids='Setup', key='instance_type')}}",
    },
    labels={"pod": POD_LABEL},
    annotations={"karpenter.sh/do-not-disrupt": "true"},
    # note: 'affinity' cannot yet be templated
    affinity=get_affinity(
        capacity_type=["spot"],
        # instance_type=["t3.2xlarge"],
        anti_affinity_label=POD_LABEL,
    ),
    on_finish_action="keep_pod",
    is_delete_operator_pod=False,
    do_xcom_push=True,
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
