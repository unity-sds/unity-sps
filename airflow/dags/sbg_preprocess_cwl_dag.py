# DAG for executing the SBG Preprocess Workflow
# See https://github.com/unity-sds/sbg-workflows/blob/main/preprocess/sbg-preprocess-workflow.cwl
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

# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}
CWL_WORKFLOW = "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.cwl"
CMR_STAC = "https://cmr.earthdata.nasa.gov/search/granules.stac?collection_concept_id=C2408009906-LPCLOUD&temporal[]=2023-08-10T03:41:03.000Z,2023-08-10T03:41:03.000Z"

dag = DAG(
    dag_id="sbg-preprocess-cwl-dag",
    description="SBG Preprocess Workflow as CWL",
    tags=["SBG", "Unity", "SPS", "NASA", "JPL"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=100,
    default_args=dag_default_args,
    params={
        "cwl_workflow": Param(CWL_WORKFLOW, type="string"),
        "input_cmr_stac": Param(CMR_STAC, type="string"),
        "input_unity_dapa_api": Param("https://d3vc8w9zcq658.cloudfront.net", type="string"),
        "input_unity_dapa_client": Param("40c2s0ulbhp9i0fmaph3su9jch", type="string"),
        "input_crid": Param("001", type="string"),
        "output_collection_id": Param("urn:nasa:unity:unity:dev:SBG-L1B_PRE___1", type="string"),
        "output_data_bucket": Param("sps-dev-ds-storage", type="string"),
    },
)


# Task that serializes the job arguments into a JSON string
def setup(ti=None, **context):
    context = get_current_context()
    dag_run_id = context["dag_run"].run_id
    local_dir = os.path.dirname(f"/shared-task-data/{dag_run_id}")
    os.makedirs(local_dir, exist_ok=True)

    task_dict = {
        "input_processing_labels": ["label1", "label2"],
        "input_cmr_stac": context["params"]["input_cmr_stac"],
        "input_unity_dapa_api": context["params"]["input_unity_dapa_api"],
        "input_unity_dapa_client": context["params"]["input_unity_dapa_client"],
        "input_crid": context["params"]["input_crid"],
        "output_collection_id": context["params"]["output_collection_id"],
        "output_data_bucket": context["params"]["output_data_bucket"],
    }
    ti.xcom_push(key="cwl_args", value=json.dumps(task_dict))


setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)


# Task that executes the specific CWL workflow with the previous arguments
cwl_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    name="SBG_Preprocess_CWL",
    on_finish_action="delete_pod",
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="SBG_Preprocess_CWL",
    full_pod_spec=k8s.V1Pod(k8s.V1ObjectMeta(name=("sbg-preprocess-cwl-pod-" + uuid.uuid4().hex))),
    pod_template_file=POD_TEMPLATE_FILE,
    arguments=["{{ params.cwl_workflow }}", "{{ti.xcom_pull(task_ids='Setup', key='cwl_args')}}", WORKING_DIR],
    dag=dag,
    volume_mounts=[
        k8s.V1VolumeMount(name="workers-volume", mount_path="/scratch", sub_path="{{ dag_run.run_id }}")
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
