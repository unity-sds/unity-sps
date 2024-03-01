# DAG for SBG Workflow #1
# See https://github.com/unity-sds/sbg-workflows/blob/main/preprocess/sbg-preprocess-workflow.cwl
import os
from datetime import datetime
from airflow import DAG
from kubernetes.client import models as k8s
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from airflow.operators.python import PythonOperator
from airflow.models.param import Param
import uuid
import json

# Fixed Parameters
UNITY_DS_IMAGE = "ghcr.io/unity-sds/unity-data-services:6.4.3"
SBG_PREPROCESS_IMAGE = "gangl/sbg-unity-preprocess:266e40d8"
COGNITO_URL = 'https://cognito-idp.us-west-2.amazonaws.com'
UNITY_USERNAME = ''
UNITY_PASSWORD = ''
UNITY_PASSWORD_TYPE = ''
DOWNLOAD_DIR = '/scratch/granules'
DOWNLOADING_KEYS = 'data, data1'
GRANULES_DOWNLOAD_TYPE = 'DAAC'

EDL_USERNAME = '/sps/processing/workflows/edl_username'
EDL_PASSWORD = '/sps/processing/workflows/edl_password'
EDL_PASSWORD_TYPE = 'PARAM_STORE'
EDL_BASE_URL = 'https://urs.earthdata.nasa.gov/'
LOG_LEVEL = '20'


# This path must be inside the shared Persistent Volume
STAC_JSON_PATH = "/scratch/search_results.json"
STAGE_IN_RESULTS = "/scratch/granules/stage-in-results.json"

# Venue dependent parameters
CLIENT_ID = '40c2s0ulbhp9i0fmaph3su9jch'
DAPA_API = 'https://d3vc8w9zcq658.cloudfront.net'
STAGING_BUCKET = 'sps-dev-ds-storage'


#CWL_URL = "http://awslbdockstorestack-lb-1429770210.us-west-2.elb.amazonaws.com:9998/api/ga4gh/trs/v2/tools/%23workflow%2Fdockstore.org%2Fmike-gangl%2FSBG-unity-preprocess/versions/16/PLAIN-CWL/descriptor/%2Fprocess.cwl"
CWL_URL = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/sbg/sbg/process.cwl"
# YAML_FILE = "/scratch/process.yaml"
ARGS = {
  "download_dir": {
    "class": "Directory",
    "path": "/scratch/granules"
  }
}

# Default DAG configuration
dag_default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1, 0, 0)
}

volume = k8s.V1Volume(
    name='unity-sps-airflow-pv',
    persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name='unity-sps-airflow-pvc')
)

volume_mount = k8s.V1VolumeMount(
    name='unity-sps-airflow-pv',
    mount_path='/scratch',
    sub_path=None,
    read_only=False
)

dag = DAG(dag_id='sbg-preprocess-no-cwl',
          description='SBG Preprocess Workflow',
          tags=["SBG", "Unity", "SPS", "NASA", "JPL"],
          is_paused_upon_creation=True,
          catchup=False,
          schedule=None,
          max_active_runs=1,
          default_args=dag_default_args,
          params={
              "input_cmr_collection_name": Param("C2408009906-LPCLOUD", type="string"),
              "input_cmr_search_start_time": Param("2023-08-10T03:41:03.000Z", type="string"),
              "input_cmr_search_stop_time": Param("2023-08-10T03:41:03.000Z", type="string"),
              "input_crid": Param("001", type="string"),
              "output_collection_id": Param("urn:nasa:unity:unity:dev:SBG-L1B_PRE___1", type="string"),
              "output_data_bucket": Param("sps-dev-ds-storage", type="string")
          }, )

cmr_query_env_vars = [
    # k8s.V1EnvVar(name="AWS_ACCESS_KEY_ID", value=""),
    # k8s.V1EnvVar(name="AWS_SECRET_ACCESS_KEY", value=""),
    # k8s.V1EnvVar(name="AWS_SESSION_TOKEN", value=""),
    # k8s.V1EnvVar(name="AWS_REGION", value=""),
    # k8s.V1EnvVar(name="UNITY_BEARER_TOKEN", value=""),
    # k8s.V1EnvVar(name="USERNAME", value=""),
    # k8s.V1EnvVar(name="PASSWORD", value=""),
    # k8s.V1EnvVar(name="PASSWORD_TYPE", value=""),
    k8s.V1EnvVar(name="CLIENT_ID", value=CLIENT_ID),
    # k8s.V1EnvVar(name="COGNITO_URL", value=COGNITO_URL),
    k8s.V1EnvVar(name="DAPA_API", value=DAPA_API),
    k8s.V1EnvVar(name="COLLECTION_ID", value="{{ params.input_cmr_collection_name }}"),
    # k8s.V1EnvVar(name="LIMITS", value=""),
    k8s.V1EnvVar(name="DATE_FROM", value="{{ params.input_cmr_search_start_time }}"),
    k8s.V1EnvVar(name="DATE_TO", value="{{ params.input_cmr_search_stop_time }}"),
    # k8s.V1EnvVar(name="VERIFY_SSL", value=""),
    k8s.V1EnvVar(name="GRANULES_SEARCH_DOMAIN", value="CMR"),
    k8s.V1EnvVar(name="CMR_BASE_URL", value="https://cmr.earthdata.nasa.gov"),
    k8s.V1EnvVar(name="LOG_LEVEL", value="20"),
    # NOTE: this is exactly the path where the KPO needs to write any xcom data
    # k8s.V1EnvVar(name="OUTPUT_FILE", value="/airflow/xcom/return.json"),
    # OR: write directly to the shared volume
    k8s.V1EnvVar(name="OUTPUT_FILE", value=STAC_JSON_PATH),
]
cmr_query_task = KubernetesPodOperator(
    image=UNITY_DS_IMAGE,
    arguments=["SEARCH"],
    env_vars=cmr_query_env_vars,
    namespace="airflow",
    name="CMR_Query",
    on_finish_action="delete_pod",
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="CMR_Query",
    full_pod_spec=k8s.V1Pod(
        k8s.V1ObjectMeta(name=('cmr-query-pod-' + uuid.uuid4().hex))),
    do_xcom_push=True,
    volumes=[volume],
    volume_mounts=[volume_mount],
    dag=dag)

stage_in_env_vars = [
    #k8s.V1EnvVar(name="AWS_ACCESS_KEY_ID", value=AWS_ACCESS_KEY_ID),
    #k8s.V1EnvVar(name="AWS_SECRET_ACCESS_KEY", value=AWS_SECRET_ACCESS_KEY),
    #k8s.V1EnvVar(name="AWS_SESSION_TOKEN", value=AWS_SESSION_TOKEN),
    #k8s.V1EnvVar(name="AWS_REGION", value=AWS_REGION),
    k8s.V1EnvVar(name="PYTHONUNBUFFERED", value="1"),
    # k8s.V1EnvVar(name="USERNAME", value=UNITY_USERNAME),
    # k8s.V1EnvVar(name="PASSWORD", value=UNITY_PASSWORD),
    # k8s.V1EnvVar(name="PASSWORD_TYPE", value=UNITY_PASSWORD_TYPE),
    k8s.V1EnvVar(name="CLIENT_ID", value=CLIENT_ID),
    k8s.V1EnvVar(name="COGNITO_URL", value=COGNITO_URL),
    k8s.V1EnvVar(name="VERIFY_SSL", value="FALSE"),
    k8s.V1EnvVar(name="STAC_AUTH_TYPE", value="UNITY"),
    k8s.V1EnvVar(name="STAC_JSON", value=STAC_JSON_PATH),
    k8s.V1EnvVar(name="DOWNLOAD_DIR", value=DOWNLOAD_DIR),
    k8s.V1EnvVar(name="DOWNLOADING_KEYS", value=DOWNLOADING_KEYS),
    # k8s.V1EnvVar(name="DOWNLOADING_ROLES", value=DOWNLOADING_ROLES),
    k8s.V1EnvVar(name="GRANULES_DOWNLOAD_TYPE", value=GRANULES_DOWNLOAD_TYPE),
    k8s.V1EnvVar(name="PARALLEL_COUNT", value="-1"),
    k8s.V1EnvVar(name="DOWNLOAD_RETRY_WAIT_TIME", value="30"),
    k8s.V1EnvVar(name="DOWNLOAD_RETRY_TIMES", value="5"),
    k8s.V1EnvVar(name="EDL_USERNAME", value=EDL_USERNAME),
    k8s.V1EnvVar(name="EDL_PASSWORD", value=EDL_PASSWORD),
    k8s.V1EnvVar(name="EDL_PASSWORD_TYPE", value=EDL_PASSWORD_TYPE),
    k8s.V1EnvVar(name="EDL_BASE_URL", value=EDL_BASE_URL),
    k8s.V1EnvVar(name="LOG_LEVEL", value=LOG_LEVEL),
    k8s.V1EnvVar(name="OUTPUT_FILE", value=STAGE_IN_RESULTS),
]
stage_in_task = KubernetesPodOperator(
    image=UNITY_DS_IMAGE,
    arguments=["DOWNLOAD"],
    env_vars=stage_in_env_vars,
    namespace="airflow",
    name="Stage_In",
    on_finish_action="delete_pod",
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="Stage_In",
    full_pod_spec=k8s.V1Pod(
        k8s.V1ObjectMeta(name=('stage-in-pod-' + uuid.uuid4().hex))),
    # do_xcom_push=True,
    volumes=[volume],
    volume_mounts=[volume_mount],
    dag=dag)


# ref:http://awslbdockstorestack-lb-1429770210.us-west-2.elb.amazonaws.com:9998/api/ga4gh/trs/v2/tools/%23workflow%2Fdockstore.org%2Fmike-gangl%2FSBG-unity-preprocess/versions/16/PLAIN-CWL/descriptor/%2Fprocess.cwl
process_task = KubernetesPodOperator(
    # image = SBG_PREPROCESS_IMAGE,
    # cmds = ["papermill", "/home/jovyan/process.ipynb", "--cwd", "/home/jovyan",
    #         os.path.join(DOWNLOAD_DIR, "process_output/output_nb.ipynb"), "-f", "/scratch/inputs.json"],
    # arguments=["-p", "input_stac_collection_file", os.path.join(DOWNLOAD_DIR, "stage-in-results.json"),
    #           "-p", "output_stac_catalog_dir", os.path.join(DOWNLOAD_DIR, "process_output")],
    pod_template_file="/opt/airflow/dags/docker_cwl_pod.yaml",
    arguments=[CWL_URL, json.dumps(ARGS), "/scratch/output_dir"],
    # env_vars=stage_in_env_vars,
    namespace="airflow",
    name="Process",
    on_finish_action="delete_pod",
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="Process",
    full_pod_spec=k8s.V1Pod(
        k8s.V1ObjectMeta(name=('process-pod-' + uuid.uuid4().hex))),
    # do_xcom_push=True,
    volumes=[volume],
    volume_mounts=[volume_mount],
    dag=dag)

stage_out_env_vars = [
    # k8s.V1EnvVar(name="AWS_ACCESS_KEY_ID", value=AWS_ACCESS_KEY_ID),
    # k8s.V1EnvVar(name="AWS_SECRET_ACCESS_KEY", value=AWS_SECRET_ACCESS_KEY),
    # k8s.V1EnvVar(name="AWS_SESSION_TOKEN", value=AWS_SESSION_TOKEN),
    # k8s.V1EnvVar(name="AWS_REGION", value=AWS_REGION),
    k8s.V1EnvVar(name="PYTHONUNBUFFERED", value="1"),
    # k8s.V1EnvVar(name="USERNAME", value=UNITY_USERNAME),
    # k8s.V1EnvVar(name="PASSWORD", value=UNITY_PASSWORD),
    # k8s.V1EnvVar(name="PASSWORD_TYPE", value=UNITY_PASSWORD_TYPE),
    k8s.V1EnvVar(name="CLIENT_ID", value=CLIENT_ID),
    k8s.V1EnvVar(name="COGNITO_URL", value=COGNITO_URL),
    k8s.V1EnvVar(name="VERIFY_SSL", value="FALSE"),
    k8s.V1EnvVar(name="DAPA_API", value=DAPA_API),
    k8s.V1EnvVar(name="COLLECTION_ID", value="{{ params.output_collection_id }}"),
    k8s.V1EnvVar(name="STAGING_BUCKET", value=STAGING_BUCKET),
    k8s.V1EnvVar(name="DELETE_FILES", value="FALSE"),
    k8s.V1EnvVar(name="GRANULES_SEARCH_DOMAIN", value="UNITY"),
    k8s.V1EnvVar(name="GRANULES_UPLOAD_TYPE", value="UPLOAD_S3_BY_STAC_CATALOG"),
    k8s.V1EnvVar(name="UPLOAD_DIR", value=""),
    k8s.V1EnvVar(name="OUTPUT_DIRECTORY", value=""),
    k8s.V1EnvVar(name="CATALOG_FILE", value="/scratch/output_dir/process_output/catalog.json"),
    k8s.V1EnvVar(name="LOG_LEVEL", value=LOG_LEVEL),
]
stage_out_task = KubernetesPodOperator(
    image=UNITY_DS_IMAGE,
    arguments=["UPLOAD"],
    env_vars=stage_out_env_vars,
    namespace="airflow",
    name="Stage_Out",
    on_finish_action="delete_pod",
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="Stage_Out",
    full_pod_spec=k8s.V1Pod(
        k8s.V1ObjectMeta(name=('stage-out-pod-' + uuid.uuid4().hex))),
    # do_xcom_push=True,
    volumes=[volume],
    volume_mounts=[volume_mount],
    dag=dag)


'''
def preprocess(ti=None, **context):
    # cmr_query = ti.xcom_pull(task_ids=['CMR_Query'])[0]
    #print(cmr_query)
    os.path.li


preprocess_task = PythonOperator(task_id="Preprocess",
                                 python_callable=preprocess,
                                 dag=dag)
'''

cmr_query_task >> stage_in_task >> process_task >> stage_out_task
