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

from airflow.models import Variable
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from airflow.operators.python import PythonOperator, get_current_context
from airflow.utils.trigger_rule import TriggerRule
from kubernetes.client import models as k8s
from unity_sps_utils import SpsKubernetesPodOperator, get_affinity

from airflow import DAG

# The Kubernetes namespace within which the Pod is run (it must already exist)
POD_NAMESPACE = "sps"
POD_LABEL = "cwl_task"
# SPS_DOCKER_CWL_IMAGE = "ghcr.io/unity-sds/unity-sps/sps-docker-cwl:2.1.0"
SPS_DOCKER_CWL_IMAGE = (
    "ghcr.io/unity-sds/unity-sps/sps-docker-cwl:186-ecr-cwl-dag"  # TODO Update with next release
)

NODE_POOL_DEFAULT = "airflow-kubernetes-pod-operator"
NODE_POOL_HIGH_WORKLOAD = "airflow-kubernetes-pod-operator-high-workload"

# The path of the working directory where the CWL workflow is executed
# (aka the starting directory for cwl-runner).
# This is fixed to the EFS /scratch directory in this DAG.
WORKING_DIR = "/scratch"

# default parameters
DEFAULT_CWL_WORKFLOW = (
    "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/main/demos/echo_message.cwl"
)
DEFAULT_CWL_ARGUMENTS = json.dumps({"message": "Hello Unity"})


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

# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}

dag = DAG(
    dag_id="cwl_dag",
    description="CWL DAG",
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
            enum=["8Gi", "16Gi", "32Gi", "64Gi", "128Gi", "256Gi"],
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
            enum=["10Gi", "50Gi", "100Gi", "200Gi", "300Gi"],
            title="Docker container storage",
        ),
        "use_ecr": Param(False, type="boolean", title="Log into AWS Elastic Container Registry (ECR)"),
    },
)


def setup(ti=None, **context):
    """
    Task that creates the working directory on the shared volume
    and parses the input parameter values.
    """
    context = get_current_context()
    dag_run_id = context["dag_run"].run_id
    local_dir = f"/shared-task-data/{dag_run_id}"
    logging.info(f"Creating directory: {local_dir}")
    os.makedirs(local_dir, exist_ok=True)
    logging.info(f"Created directory: {local_dir}")

    # select the node pool based on what resources were requested
    node_pool = NODE_POOL_DEFAULT
    storage = context["params"]["request_storage"]  # 100Gi
    storage = int(storage[0:-2])  # 100
    memory = context["params"]["request_memory"]  # 32Gi
    memory = int(memory[0:-2])  # 32
    cpu = int(context["params"]["request_cpu"])  # 8

    logging.info(f"Requesting storage={storage}Gi memory={memory}Gi CPU={cpu}")
    if (storage > 30) or (memory > 32) or (cpu > 8):
        node_pool = NODE_POOL_HIGH_WORKLOAD
    logging.info(f"Selecting node pool={node_pool}")
    ti.xcom_push(key="node_pool", value=node_pool)

    # select arguments and determine if ECR login is required
    cwl_dag_args = json.loads(context["params"]["cwl_args"])
    logging.info("Use ECR: %s", context["params"]["use_ecr"])
    if context["params"]["use_ecr"]:
        ecr_uri = Variable.get("cwl_dag_ecr_uri")
        cwl_dag_args["cwltool:overrides"] = {
            context["params"]["cwl_workflow"]: {
                "requirements": {"DockerRequirement": {"dockerPull": ecr_uri}}
            }
        }
        ecr_login = ecr_uri.split("/")[0]
        ti.xcom_push(key="ecr_login", value=ecr_login)
        logging.info("ECR login: %s", ecr_login)
    ti.xcom_push(key="cwl_dag_arguments", value=json.dumps(cwl_dag_args))
    logging.info("CWL DAG arguments: %s", cwl_dag_args)


setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)

cwl_task = SpsKubernetesPodOperator(
    retries=0,
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
        "{{ ti.xcom_pull(task_ids='Setup', key='cwl_dag_arguments') }}",
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
    node_selector={"karpenter.sh/nodepool": "{{ti.xcom_pull(task_ids='Setup', key='node_pool')}}"},
    labels={"app": POD_LABEL},
    annotations={"karpenter.sh/do-not-disrupt": "true"},
    # note: 'affinity' cannot yet be templated
    affinity=get_affinity(
        capacity_type=["spot"],
        # instance_type=["t3.2xlarge"],
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
        shutil.rmtree(local_dir)
        logging.info(f"Deleted directory: {local_dir}")
    else:
        logging.info(f"Directory does not exist, no need to delete: {local_dir}")


cleanup_task = PythonOperator(
    task_id="Cleanup", python_callable=cleanup, dag=dag, trigger_rule=TriggerRule.ALL_DONE
)

chain(setup_task, cwl_task, cleanup_task)
