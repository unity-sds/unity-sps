"""
DAG to execute a generic CWL workflow using the "high-workload" Karpenter node pool.
Default parameters are set for the DBG end-to-end L1 to L2 CWL workflow.

The Airflow KubernetesPodOperator starts a Docker container that includes the Docker engine and the CWL libraries.
The "cwl-runner" tool is invoked to execute the CWL workflow.
Parameter cwl_workflow: the URL of the CWL workflow to execute.
Parameter args_as_json: JSON string contained the specific values for the workflow specific inputs.
"""

# import json
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
from unity_sps_utils import get_affinity

from airflow import DAG

# The Kubernetes namespace within which the Pod is run (it must already exist)
POD_NAMESPACE = "airflow"
POD_LABEL = "cwl_high_workload_task"
SPS_DOCKER_CWL_IMAGE = "ghcr.io/unity-sds/unity-sps/sps-docker-cwl:2.1.0"
NODE_POOL = "airflow-kubernetes-pod-operator-high-workload"
EC2_TYPE = "c5.9xlarge"

# The path of the working directory where the CWL workflow is executed
# (aka the starting directory for cwl-runner).
# This is fixed to the EFS /scratch directory in this DAG.
WORKING_DIR = "/scratch"

# Alternative arguments to execute SBG Pre-Process
# DEFAULT_CWL_WORKFLOW =  "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.cwl"
# DEFAULT_CWL_ARGUMENTS = "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.dev.yml"

# Alternative arguments to execute SBG end-to-end
DEFAULT_CWL_WORKFLOW = "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/L1-to-L2-e2e.cwl"
DEFAULT_CWL_ARGUMENTS = "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/L1-to-L2-e2e.dev.yml"

# Alternative arguments to execute SBG end-to-end
# unity_sps_sbg_debug.txt
CONTAINER_RESOURCES = k8s.V1ResourceRequirements(
    requests={
        # "cpu": "2660m",  # 2.67 vCPUs, specified in milliCPUs
        # "memory": "22Gi",  # Rounded to 22 GiB for easier specification
        "ephemeral-storage": "50Gi"
    },
)

# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}

# common parameters
INPUT_PROCESSING_LABELS = ["label1", "label2"]

dag = DAG(
    dag_id="cwl_high_workload_dag",
    description="CWL High Workload DAG",
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
            description="The job parameters encoded as a JSON string, or the URL of a JSON or YAML file",
        ),
    },
)


def setup(ti=None, **context):
    """
    Task that creates the working directory on the shared volume.
    """
    context = get_current_context()
    dag_run_id = context["dag_run"].run_id
    local_dir = f"/shared-task-data/{dag_run_id}"
    logging.info(f"Creating directory: {local_dir}")
    os.makedirs(local_dir, exist_ok=True)
    logging.info(f"Created directory: {local_dir}")


setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)

cwl_task = KubernetesPodOperator(
    retries=0,
    task_id="cwl_high_workload_task",
    namespace=POD_NAMESPACE,
    name="cwl-high_workload-task-pod",
    image=SPS_DOCKER_CWL_IMAGE,
    service_account_name="airflow-worker",
    in_cluster=True,
    get_logs=True,
    startup_timeout_seconds=1800,
    arguments=["{{ params.cwl_workflow }}", "{{ params.cwl_args }}"],
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
    node_selector={"karpenter.sh/nodepool": NODE_POOL},
    labels={"app": POD_LABEL},
    annotations={"karpenter.sh/do-not-disrupt": "true"},
    affinity=get_affinity(
        capacity_type=["spot"],
        instance_type=[EC2_TYPE],
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
