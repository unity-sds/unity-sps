# DAG for executing the SBG L1-to-L2 End-To-End Workflow
# See https://github.com/unity-sds/sbg-workflows/blob/main/L1-to-L2-e2e.cwl
import json
import uuid
from datetime import datetime

from airflow.models.param import Param
from airflow.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s

from airflow import DAG

# The Kubernetes Pod that executes the CWL-Docker container
# Must use elevated privileges to start/stop the Docker engine
POD_TEMPLATE_FILE = "/opt/airflow/dags/docker_cwl_pod.yaml"

# The Kubernetes namespace within which the Pod is run (it must already exist)
POD_NAMESPACE = "sps"

# The path of the working directory where the CWL workflow is executed
# (aka the starting directory for cwl-runner).
# This is fixed to the EFS /scratch directory in this DAG.
WORKING_DIR = "/scratch"

# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}
CWL_WORKFLOW = "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/L1-to-L2-e2e.cwl"
INPUT_AUX_STAC = '{"numberMatched":{"total_size":1},"numberReturned":1,"stac_version":"1.0.0","type":"FeatureCollection","links":[{"rel":"self","href":"https://d3vc8w9zcq658.cloudfront.net/am-uds-dapa/collections/urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/items?limit=10"},{"rel":"root","href":"https://d3vc8w9zcq658.cloudfront.net"}],"features":[{"type":"Feature","stac_version":"1.0.0","id":"urn:nasa:unity:unity:dev:SBG-AUX___1:sRTMnet_v120","properties":{"datetime":"2024-02-14T22:04:41.078000Z","start_datetime":"2024-01-03T13:19:36Z","end_datetime":"2024-01-03T13:19:48Z","created":"2024-01-03T13:19:36Z","updated":"2024-02-14T22:05:25.248000Z","status":"completed","provider":"unity"},"geometry":{"type":"Point","coordinates":[0,0]},"links":[{"rel":"collection","href":"."}],"assets":{"sRTMnet_v120.h5":{"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-AUX___1/urn:nasa:unity:unity:dev:SBG-AUX___1:sRTMnet_v120.h5/sRTMnet_v120.h5","title":"sRTMnet_v120.h5","description":"size=-1;checksumType=md5;checksum=unknown;","roles":["data"]},"sRTMnet_v120_aux.npz":{"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-AUX___1/urn:nasa:unity:unity:dev:SBG-AUX___1:sRTMnet_v120.h5/sRTMnet_v120_aux.npz","title":"sRTMnet_v120_aux.npz","description":"size=-1;checksumType=md5;checksum=unknown;","roles":["data"]}},"bbox":[-180,-90,180,90],"stac_extensions":[],"collection":"urn:nasa:unity:unity:dev:SBG-AUX___1"}]}'

dag = DAG(
    dag_id="sbg_L1_to_L2_e2e_cwl_dag",
    description="SBG L1 to L2 End-To-End Workflow as CWL",
    tags=["SBG", "Unity", "SPS", "NASA", "JPL"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=100,
    default_args=dag_default_args,
    params={
        "cwl_workflow": Param(CWL_WORKFLOW, type="string"),
        # For CMR Search Step
        "input_cmr_collection_name": Param("C2408009906-LPCLOUD", type="string"),
        "input_cmr_search_start_time": Param("2024-01-03T13:19:36.000Z", type="string"),
        "input_cmr_search_stop_time": Param("2024-01-03T13:19:36.000Z", type="string"),
        # U-DS config
        "input_unity_dapa_api": Param("https://d3vc8w9zcq658.cloudfront.net", type="string"),
        "input_unity_dapa_client": Param("40c2s0ulbhp9i0fmaph3su9jch", type="string"),
        #
        "input_crid": Param("001", type="string"),
        # For unity data upload step, unity catalog
        "output_preprocess_collection_id": Param("40c2s0ulbhp9i0fmaph3su9jch", type="string"),
        "output_data_bucket": Param("sps-dev-ds-storage", type="string"),
        "input_aux_stac": Param(INPUT_AUX_STAC, type="string"),
        # For unity data upload step, unity catalog
        "output_isofit_collection_id": Param("urn:nasa:unity:unity:dev:SBG-L2A_RFL___1", type="string"),
        "output_resample_collection_id": Param("urn:nasa:unity:unity:dev:SBG-L2A_RSRFL___1", type="string"),
        "output_refcorrect_collection_id": Param("urn:nasa:unity:unity:dev:SBG-L2A_CORFL___1", type="string"),
    },
)


# Task that serializes the job arguments into a JSON string
def setup(ti=None, **context):
    task_dict = {
        "input_processing_labels": ["label1", "label2"],
        "input_cmr_collection_name": context["params"]["input_cmr_collection_name"],
        "input_cmr_search_start_time": context["params"]["input_cmr_search_start_time"],
        "input_cmr_search_stop_time": context["params"]["input_cmr_search_stop_time"],
        "input_unity_dapa_api": context["params"]["input_unity_dapa_api"],
        "input_unity_dapa_client": context["params"]["input_unity_dapa_client"],
        "input_crid": context["params"]["input_crid"],
        "output_preprocess_collection_id": context["params"]["output_preprocess_collection_id"],
        "output_data_bucket": context["params"]["output_data_bucket"],
        "input_aux_stac": context["params"]["input_aux_stac"],
        "output_isofit_collection_id": context["params"]["output_isofit_collection_id"],
        "output_resample_collection_id": context["params"]["output_resample_collection_id"],
        "output_refcorrect_collection_id": context["params"]["output_refcorrect_collection_id"],
    }
    ti.xcom_push(key="cwl_args", value=json.dumps(task_dict))


setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)


# Task that executes the specific CWL workflow with the previous arguments
cwl_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    name="SBG_L1_to_L2_End_To_End_CWL",
    on_finish_action="delete_pod",
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="SBG_L1_to_L2_End_To_End_CWL",
    full_pod_spec=k8s.V1Pod(k8s.V1ObjectMeta(name=("sbg-l1-to-l2-e2e-cwl-pod-" + uuid.uuid4().hex))),
    pod_template_file=POD_TEMPLATE_FILE,
    arguments=["{{ params.cwl_workflow }}", "{{ti.xcom_pull(task_ids='Setup', key='cwl_args')}}"],
    # resources={"request_memory": "512Mi", "limit_memory": "1024Mi"},
    dag=dag,
)

setup_task >> cwl_task
