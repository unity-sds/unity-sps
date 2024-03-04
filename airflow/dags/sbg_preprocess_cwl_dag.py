# DAG for executing the SBG Preprocess Workflow
# See https://github.com/unity-sds/sbg-workflows/blob/main/preprocess/sbg-preprocess-workflow.cwl
import json
import uuid
from datetime import datetime

from airflow.models.param import Param
from airflow.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from kubernetes.client import models as k8s

from airflow import DAG

# The Kubernetes Pod that executes the CWL-Docker container
# Must use elevated privileges to start/stop the Docker engine
POD_TEMPLATE_FILE = "/opt/airflow/dags/docker_cwl_pod.yaml"

# The Kubernetes namespace within which the Pod is run (it must already exist)
POD_NAMESPACE = "airflow"


# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}
CWL_WORKFLOW = (
    "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.cwl"
)
CMR_STAC = "https://cmr.earthdata.nasa.gov/search/granules.stac?collection_concept_id=C2408009906-LPCLOUD&temporal[]=2023-08-10T03:41:03.000Z,2023-08-10T03:41:03.000Z"

dag = DAG(
    dag_id="sbg-preprocess-cwl-dag",
    description="SBG Preprocess Workflow as CWL",
    tags=["SBG", "Unity", "SPS", "NASA", "JPL"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=1,
    default_args=dag_default_args,
    params={
        "cwl_workflow": Param(CWL_WORKFLOW, type="string"),
        "input_cmr_stac": Param(CMR_STAC, type="string"),
        # "input_processing_labels": Param(["label1", "label2"], type="string[]"),
        # "input_cmr_collection_name": Param("C2408009906-LPCLOUD", type="string"),
        # "input_cmr_search_start_time": Param("2024-01-03T13:19:36.000Z", type="string"),
        # "input_cmr_search_stop_time": Param("2024-01-03T13:19:36.000Z", type="string"),
        "input_unity_dapa_api": Param("https://d3vc8w9zcq658.cloudfront.net", type="string"),
        "input_unity_dapa_client": Param("40c2s0ulbhp9i0fmaph3su9jch", type="string"),
        "input_crid": Param("001", type="string"),
        "output_collection_id": Param("urn:nasa:unity:unity:dev:SBG-L1B_PRE___1", type="string"),
        "output_data_bucket": Param("sps-dev-ds-storage", type="string"),
    },
)


# Task that serializes the job arguments into a JSON string
def setup(ti=None, **context):
    task_dict = {
        "input_processing_labels": ["label1", "label2"],
        "input_cmr_stac": context["params"]["input_cmr_stac"],
        # "input_cmr_collection_name": context["params"]["input_cmr_collection_name"],
        # "input_cmr_search_start_time": context["params"]["input_cmr_search_start_time"],
        # "input_cmr_search_stop_time": context["params"]["input_cmr_search_stop_time"],
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
    arguments=["{{ params.cwl_workflow }}", "{{ti.xcom_pull(task_ids='Setup', key='cwl_args')}}"],
    # resources={"request_memory": "512Mi", "limit_memory": "1024Mi"},
    dag=dag,
)

setup_task >> cwl_task
