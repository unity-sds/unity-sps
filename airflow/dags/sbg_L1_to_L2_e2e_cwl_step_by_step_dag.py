# DAG for executing the SBG L1-to-L2 End-To-End Workflow
# See https://github.com/unity-sds/sbg-workflows/blob/main/L1-to-L2-e2e.cwl
import json
import uuid
from datetime import datetime
import os
import shutil

from airflow.models.param import Param
from airflow.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from kubernetes.client import models as k8s
from airflow.utils.trigger_rule import TriggerRule

from airflow import DAG

# The Kubernetes Pod that executes the CWL-Docker container
# Must use elevated privileges to start/stop the Docker engine
POD_TEMPLATE_FILE = "/opt/airflow/dags/docker_cwl_pod.yaml"

# The Kubernetes namespace within which the Pod is run (it must already exist)
POD_NAMESPACE = "airflow"

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

PREPROCESS_INPUT_AUX_STAC = 'https://cmr.earthdata.nasa.gov/search/granules.stac?collection_concept_id=C2408009906-LPCLOUD&temporal[]=2023-08-10T03:41:03.000Z,2023-08-10T03:41:03.000Z'
ISOFIT_INPUT_STAC = "https://d3vc8w9zcq658.cloudfront.net/am-uds-dapa/collections/urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/items?filter=start_datetime%20%3E%3D%20%272024-01-03T13%3A19%3A34Z%27%20AND%20start_datetime%20%3C%3D%20%272024-01-03T13%3A19%3A36Z%27"
ISOFIT_INPUT_AUX_STAC = '{"numberMatched":{"total_size":1},"numberReturned":1,"stac_version":"1.0.0","type":"FeatureCollection","links":[{"rel":"self","href":"https://d3vc8w9zcq658.cloudfront.net/am-uds-dapa/collections/urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/items?limit=10"},{"rel":"root","href":"https://d3vc8w9zcq658.cloudfront.net"}],"features":[{"type":"Feature","stac_version":"1.0.0","id":"urn:nasa:unity:unity:dev:SBG-AUX___1:sRTMnet_v120","properties":{"datetime":"2024-02-14T22:04:41.078000Z","start_datetime":"2024-01-03T13:19:36Z","end_datetime":"2024-01-03T13:19:48Z","created":"2024-01-03T13:19:36Z","updated":"2024-02-14T22:05:25.248000Z","status":"completed","provider":"unity"},"geometry":{"type":"Point","coordinates":[0,0]},"links":[{"rel":"collection","href":"."}],"assets":{"sRTMnet_v120.h5":{"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-AUX___1/urn:nasa:unity:unity:dev:SBG-AUX___1:sRTMnet_v120.h5/sRTMnet_v120.h5","title":"sRTMnet_v120.h5","description":"size=-1;checksumType=md5;checksum=unknown;","roles":["data"]},"sRTMnet_v120_aux.npz":{"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-AUX___1/urn:nasa:unity:unity:dev:SBG-AUX___1:sRTMnet_v120.h5/sRTMnet_v120_aux.npz","title":"sRTMnet_v120_aux.npz","description":"size=-1;checksumType=md5;checksum=unknown;","roles":["data"]}},"bbox":[-180,-90,180,90],"stac_extensions":[],"collection":"urn:nasa:unity:unity:dev:SBG-AUX___1"}]}'
ISOFIT_OUTPUT_COLLECTION_ID = "urn:nasa:unity:unity:dev:SBG-L2A_RFL___1"

DAPA_CLIENT_DEV_VENUE = "40c2s0ulbhp9i0fmaph3su9jch"
DAPA_API_DEV_VENUE = "https://d3vc8w9zcq658.cloudfront.net"
PREPROCESS_OUTPUT_COLLECTION_ID = "urn:nasa:unity:unity:dev:SBG-L1B_PRE___1"
OUTPUT_DATA_BUCKET = "sps-dev-ds-storage"

dag = DAG(
    dag_id="sbg-l1-to-l2-e2e-cwl-step-by-step-dag",
    description="SBG L1 to L2 End-To-End Workflow as step-by-step CWL DAGs",
    tags=["SBG", "Unity", "SPS", "NASA", "JPL"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=100,
    default_args=dag_default_args,
    params={

        # step: CMR
        "input_cmr_collection_name": Param("C2408009906-LPCLOUD", type="string"),
        "input_cmr_search_start_time": Param("2024-01-03T13:19:36.000Z", type="string"),
        "input_cmr_search_stop_time": Param("2024-01-03T13:19:36.000Z", type="string"),

        # step: PREPROCESS
        # "preprocess_input_cmr_stac": Param(PREPROCESS_INPUT_AUX_STAC, type="string"),
        "preprocess_output_collection_id": Param(PREPROCESS_OUTPUT_COLLECTION_ID, type="string"),

        # step: PREPROCESS DATA CATALOG

        # step: ISOFIT
        # "isofit_input_cmr_collection_name": Param("C2408009906-LPCLOUD", type="string"),
        # "isofit_input_cmr_search_start_time": Param("2024-01-03T13:19:36.000Z", type="string"),
        # "isofit_input_cmr_search_stop_time": Param("2024-01-03T13:19:36.000Z", type="string"),
        "isofit_input_stac": Param(ISOFIT_INPUT_STAC, type="string"),
        "isofit_input_aux_stac": Param(ISOFIT_INPUT_AUX_STAC, type="string"),
        "isofit_output_collection_id": Param(ISOFIT_OUTPUT_COLLECTION_ID, type="string"),

        # For all steps
        "input_unity_dapa_client": Param(DAPA_CLIENT_DEV_VENUE, type="string"),
        "input_unity_dapa_api": Param(DAPA_API_DEV_VENUE, type="string"),
        "output_data_bucket": Param(OUTPUT_DATA_BUCKET, type="string"),
        "input_crid": Param("001", type="string"),
        "unity_stac_auth": Param("UNITY", type="string"),

    },
)


# Step: Setup
# Task that serializes the job arguments into a JSON string
def setup(ti=None, **context):

    cmr_dict = {
        "cmr_collection": context["params"]["input_cmr_collection_name"],
        "cmr_start_time": context["params"]["input_cmr_search_start_time"],
        "cmr_stop_time": context["params"]["input_cmr_search_stop_time"],
    }
    ti.xcom_push(key="cmr_query_args", value=json.dumps(cmr_dict))

    preprocess_dict = {
        "input_processing_labels": ["label1", "label2"],
        "input_cmr_stac": "/scratch/cmr-results.json",
        "input_unity_dapa_client": context["params"]["input_unity_dapa_client"],
        "input_unity_dapa_api": context["params"]["input_unity_dapa_api"],
        "input_crid": context["params"]["input_crid"],
        "output_collection_id": context["params"]["preprocess_output_collection_id"],
        "output_data_bucket": context["params"]["output_data_bucket"],
    }
    ti.xcom_push(key="preprocess_args", value=json.dumps(preprocess_dict))

    isofit_dict = {
        "input_processing_labels": ["label1", "label2"],
        "input_cmr_collection_name": context["params"]["input_cmr_collection_name"],
        "input_cmr_search_start_time": context["params"]["input_cmr_search_start_time"],
        "input_cmr_search_stop_time": context["params"]["input_cmr_search_stop_time"],
        "input_stac": context["params"]["isofit_input_stac"],
        "unity_stac_auth": context["params"]["unity_stac_auth"],
        "input_aux_stac": context["params"]["isofit_input_aux_stac"],
        "input_unity_dapa_client": context["params"]["input_unity_dapa_client"],
        "input_unity_dapa_api": context["params"]["input_unity_dapa_api"],
        "input_crid": context["params"]["input_crid"],
        "output_collection_id": context["params"]["isofit_output_collection_id"],
        "output_data_bucket": context["params"]["output_data_bucket"],
    }
    ti.xcom_push(key="isofit_args", value=json.dumps(isofit_dict))


setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)

# Step: CMR
SBG_CMR_WORKFLOW = "http://awslbdockstorestack-lb-1429770210.us-west-2.elb.amazonaws.com:9998/api/ga4gh/trs/v2/tools/%23workflow%2Fdockstore.org%2Fmike-gangl%2Fcmr-trial/versions/4/PLAIN-CWL/descriptor/%2FDockstore.cwl"
cmr_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    name="CMR_Query",
    on_finish_action="delete_pod",
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="SBG_CMR_Query",
    full_pod_spec=k8s.V1Pod(k8s.V1ObjectMeta(name=("sbg-cmr-query-pod-" + uuid.uuid4().hex))),
    pod_template_file=POD_TEMPLATE_FILE,
    arguments=[
        SBG_CMR_WORKFLOW,
        "{{ti.xcom_pull(task_ids='Setup', key='cmr_query_args')}}",
        WORKING_DIR,
    ],
    volume_mounts=[
        k8s.V1VolumeMount(name="workers-volume", mount_path=WORKING_DIR, sub_path="{{ dag_run.run_id }}")
    ],
    volumes=[
        k8s.V1Volume(
            name="workers-volume",
            persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="kpo-efs"),
        )
    ],
    dag=dag,
)

# Step: PREPROCESS
SBG_PREPROCESS_CWL = "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.cwl"
preprocess_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    name="Preprocess",
    on_finish_action="delete_pod",
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="SBG_Preprocess",
    full_pod_spec=k8s.V1Pod(k8s.V1ObjectMeta(name=("sbg-preprocess-pod-" + uuid.uuid4().hex))),
    pod_template_file=POD_TEMPLATE_FILE,
    arguments=[
        SBG_PREPROCESS_CWL,
        "{{ti.xcom_pull(task_ids='Setup', key='preprocess_args')}}",
        WORKING_DIR,
    ],
    volume_mounts=[
        k8s.V1VolumeMount(name="workers-volume", mount_path=WORKING_DIR, sub_path="{{ dag_run.run_id }}")
    ],
    volumes=[
        k8s.V1Volume(
            name="workers-volume",
            persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="kpo-efs"),
        )
    ],
    dag=dag,
)

# Step: ISOFIT
SBG_ISOFIT_CWL = "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/isofit/sbg-isofit-workflow.cwl"
isofit_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    name="Isofit",
    on_finish_action="delete_pod",
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="SBG_Isofit",
    full_pod_spec=k8s.V1Pod(k8s.V1ObjectMeta(name=("sbg-isofit-pod-" + uuid.uuid4().hex))),
    pod_template_file=POD_TEMPLATE_FILE,
    arguments=[
        SBG_ISOFIT_CWL,
        "{{ti.xcom_pull(task_ids='Setup', key='isofit_args')}}",
        WORKING_DIR,
    ],
    volume_mounts=[
        k8s.V1VolumeMount(name="workers-volume", mount_path=WORKING_DIR, sub_path="{{ dag_run.run_id }}")
    ],
    volumes=[
        k8s.V1Volume(
            name="workers-volume",
            persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="kpo-efs"),
        )
    ],
    dag=dag,
)

def cleanup(**context):
    dag_run_id = context["dag_run"].run_id
    local_dir = f"/shared-task-data/{dag_run_id}"
    if os.path.exists(local_dir):
        shutil.rmtree(local_dir)
        print(f"Deleted directory: {local_dir}")
    else:
        print(f"Directory does not exist, no need to delete: {local_dir}")

# The cleanup task will run as long as at lest the Setup task succeeds
cleanup_task = PythonOperator(
    task_id="Cleanup",
    python_callable=cleanup,
    trigger_rule=TriggerRule.ONE_SUCCESS,
    dag=dag,
)

setup_task >> preprocess_task >> isofit_task >> cleanup_task
