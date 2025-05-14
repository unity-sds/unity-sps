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
import shutil
from datetime import datetime

from airflow.models.baseoperator import chain
from airflow.models.param import Param
from airflow.operators.python import PythonOperator, get_current_context
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.utils.trigger_rule import TriggerRule
from kubernetes.client import models as k8s
from unity_sps_utils import (
    DEFAULT_LOG_LEVEL,
    EC2_TYPES,
    LOG_LEVEL_TYPE,
    NODE_POOL_DEFAULT,
    NODE_POOL_HIGH_WORKLOAD,
    POD_LABEL,
    POD_NAMESPACE,
    SPS_DOCKER_CWL_IMAGE,
    build_ec2_type_label,
    get_affinity,
)

from airflow import DAG

# The path of the working directory where the CWL workflow is executed
# (aka the starting directory for cwl-runner).
# This is fixed to the EFS /scratch directory in this DAG.
# WORKING_DIR = "/scratch"
WORKING_DIR = "/data"


# default parameters
DEFAULT_CWL_WORKFLOW = (
    "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/main/demos/echo_message.cwl"
)
DEFAULT_CWL_ARGUMENTS = json.dumps({"message": "Hello Unity"})

CONTAINER_RESOURCES = k8s.V1ResourceRequirements(
    requests={
        "ephemeral-storage": "{{ params.request_storage }} ",
    }
)

# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}

dag = DAG(
    dag_id="cwl_dag",
    description="CWL DAG",
    dag_display_name="CWL DAG",
    tags=["CWL"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=1000,
    max_active_tasks=3000,
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
        "log_level": Param(
            DEFAULT_LOG_LEVEL,
            type="string",
            enum=list(LOG_LEVEL_TYPE.keys()),
            title="Processing log levels",
            description=("Log level for DAG processing"),
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
    },
)


def setup(ti=None, **context):
    """
    Task that creates the working directory on the shared volume
    and parses the input parameter values.
    """
    context = get_current_context()
    logging.info(f"DAG Run parameters: {json.dumps(context['params'], sort_keys=True, indent=4)}")

    dag_run_id = context["dag_run"].run_id
    local_dir = f"/shared-task-data/{dag_run_id}"
    logging.info(f"Creating directory: {local_dir}")
    os.makedirs(local_dir, exist_ok=True)
    logging.info(f"Created directory: {local_dir}")

    # select the node pool based on what resources were requested
    node_pool = NODE_POOL_DEFAULT
    storage = context["params"]["request_storage"]  # 100Gi
    container_storage = int(storage[0:-2])  # 100
    ti.xcom_push(key="container_storage", value=container_storage)

    # from "t3.large (General Purpose: 2vCPU, 8GiB)" to "t3.large"
    instance_type = context["params"]["request_instance_type"]
    cpu = EC2_TYPES[instance_type]["cpu"]
    memory = EC2_TYPES[instance_type]["memory"]
    ti.xcom_push(key="instance_type", value=instance_type)
    logging.info(f"Requesting EC2 instance type={instance_type}")

    logging.info(f"Requesting container storage={container_storage}Gi")
    if (container_storage > 30) or (cpu > 16) or (memory > 32):
        node_pool = NODE_POOL_HIGH_WORKLOAD
    logging.info(f"Selecting node pool={node_pool}")
    ti.xcom_push(key="node_pool", value=node_pool)

    # select ECR login URL
    ecr_login = os.environ["AIRFLOW_VAR_ECR_URI"]
    ti.xcom_push(key="ecr_login", value=ecr_login)
    logging.info("ECR login: %s", ecr_login)

    # select log level based on debug
    log_level = context["params"]["log_level"]
    ti.xcom_push(key="log_level", value=LOG_LEVEL_TYPE[log_level])
    logging.info(f"Selecting log level: {LOG_LEVEL_TYPE[log_level]}.")


setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag, weight_rule="upstream")

cwl_task = KubernetesPodOperator(
    retries=1,
    weight_rule="upstream",
    task_id="cwl_task",
    namespace=POD_NAMESPACE,
    name="cwl-task-pod",
    image=SPS_DOCKER_CWL_IMAGE,
    service_account_name="airflow-worker",
    in_cluster=True,
    get_logs=True,
    startup_timeout_seconds=1800,
    arguments=[
        "-w",
        "{{ params.cwl_workflow }}",
        "-j",
        "{{ params.cwl_args }}",
        "-l",
        "{{ ti.xcom_pull(task_ids='Setup', key='log_level') }}",
        "-e",
        "{{ ti.xcom_pull(task_ids='Setup', key='ecr_login') }}",
    ],
    container_security_context={"privileged": True},
    container_resources=k8s.V1ResourceRequirements(
        requests={
            "ephemeral-storage": "{{ti.xcom_pull(task_ids='Setup', key='container_storage')}}",
        },
    ),
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
    volume_mounts=[
        k8s.V1VolumeMount(name="workers-data", mount_path=WORKING_DIR),
        k8s.V1VolumeMount(name="workers-docker", mount_path="/var/lib/docker/"),
    ],
    volumes=[
        k8s.V1Volume(
            name="workers-data",
            empty_dir=k8s.V1EmptyDirVolumeSource(medium=""),
        ),
        k8s.V1Volume(
            name="workers-docker",
            empty_dir=k8s.V1EmptyDirVolumeSource(medium=""),
        ),
    ],
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
        # instance_type=["r7i.2xlarge"],
        anti_affinity_label=POD_LABEL,
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
    local_dir = f"/shared-task-data/{dag_run_id}"
    if os.path.exists(local_dir):
        logging.info(f"Content of directory: {local_dir}")
        files = os.listdir(local_dir)
        for f in files:
            logging.info(os.path.join(local_dir, f))
        shutil.rmtree(local_dir)
        logging.info(f"Deleted directory: {local_dir}")
    else:
        logging.info(f"Directory does not exist, no need to delete: {local_dir}")


cleanup_task = PythonOperator(
    task_id="Cleanup",
    python_callable=cleanup,
    dag=dag,
    trigger_rule=TriggerRule.ALL_DONE,
    weight_rule="upstream",
)

chain(setup_task.as_setup(), cwl_task, cleanup_task.as_teardown(setups=setup_task))
