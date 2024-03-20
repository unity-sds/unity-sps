# DAG to execute a generic CWL workflow.
# The Airflow KubernetesPodOperator starts a Docker container that includes the Docker engine and the CWL libraries.
# The "cwl-runner" tool is invoked to execute the CWL workflow.
# Parameter cwl_workflow: the URL of the CWL workflow to execute.
# Parameter args_as_json: JSON string contained the specific values for the workflow specific inputs.
import json
import os
import shutil
import uuid
from datetime import datetime

from airflow.models.param import Param
from airflow.operators.python import PythonOperator, get_current_context
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from kubernetes.client import models as k8s

from airflow import DAG

# The Kubernetes Pod that executes the CWL-Docker container
# Must use elevated privileges to start/stop the Docker engine
POD_TEMPLATE_FILE = "/opt/airflow/dags/docker_cwl_pod.yaml"

# The Kubernetes namespace within which the Pod is run (it must already exist)
POD_NAMESPACE = "airflow"

# The path of the working directory where the CWL workflow is executed
# (aka the starting directory for cwl-runner)
WORKING_DIR = "/scratch"

# Example arguments
default_cwl_workflow = (
    "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.cwl"
)
# default_cwl_args = "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.dev.yml"
default_cwl_args = {
    "input_processing_labels": ["label1", "label2"],
    "input_cmr_stac": "https://cmr.earthdata.nasa.gov/search/granules.stac?collection_concept_id=C2408009906-LPCLOUD&temporal[]=2023-08-10T03:41:03.000Z,2023-08-10T03:41:03.000Z",
    "input_unity_dapa_client": "40c2s0ulbhp9i0fmaph3su9jch",
    "input_unity_dapa_api": "https://d3vc8w9zcq658.cloudfront.net",
    "input_crid": "001",
    "output_collection_id": "urn:nasa:unity:unity:dev:SBG-L1B_PRE___1",
    "output_data_bucket": "sps-dev-ds-storage",
}

# Default DAG configuration
dag_default_args = {"owner": "unity-sps", "depends_on_past": False, "start_date": datetime(2024, 1, 1, 0, 0)}

# The DAG
dag = DAG(
    dag_id="cwl-dag",
    description="DAG to execute a generic CWL workflow",
    tags=["cwl", "unity-sps", "docker"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule_interval=None,
    max_active_runs=100,
    default_args=dag_default_args,
    params={
        "cwl_workflow": Param(
            default_cwl_workflow, type="string", title="CWL workflow", description="The CWL workflow URL"
        ),
        "cwl_args": Param(
            json.dumps(default_cwl_args),
            type="string",
            title="CWL workflow parameters",
            description="The job parameters encodes as a JSON string, or the URL of a JSON or YAML file",
        )
    },
)

# Environment variables
default_env_vars = {}


# This task that creates the working directory on the shared volume
def setup(ti=None, **context):
    context = get_current_context()
    dag_run_id = context["dag_run"].run_id
    local_dir = os.path.dirname(f"/shared-task-data/{dag_run_id}")
    os.makedirs(local_dir, exist_ok=True)


setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)

# This section defines KubernetesPodOperator
cwl_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    name="cwl-task",
    is_delete_operator_pod=True,
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="docker-cwl-task",
    full_pod_spec=k8s.V1Pod(
        metadata=k8s.V1ObjectMeta(name="docker-cwl-pod-" + uuid.uuid4().hex),
    ),
    pod_template_file=POD_TEMPLATE_FILE,
    arguments=["{{ params.cwl_workflow }}", "{{ params.cwl_args }}"],
    dag=dag,
    volume_mounts=[
        k8s.V1VolumeMount(name="workers-volume", mount_path=WORKING_DIR, sub_path="{{ dag_run.run_id }}")
    ],
    volumes=[
        k8s.V1Volume(
            name="workers-volume",
            persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="kpo-efs"),
        )
    ],
)


def cleanup(**context):
    dag_run_id = context["dag_run"].run_id
    local_dir = f"/shared-task-data/{dag_run_id}"
    if os.path.exists(local_dir):
        shutil.rmtree(local_dir)
        print(f"Deleted directory: {local_dir}")
    else:
        print(f"Directory does not exist, no need to delete: {local_dir}")


cleanup_task = PythonOperator(
    task_id="Cleanup",
    python_callable=cleanup,
    dag=dag,
)

setup_task >> cwl_task >> cleanup_task
