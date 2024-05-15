"""
DAG for executing the SBG L1-to-L2 End-To-End Workflow.
See https://github.com/unity-sds/sbg-workflows/blob/main/L1-to-L2-e2e.cwl.
"""

import json
import logging
import os
import shutil
import uuid
from datetime import datetime

import boto3
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from airflow.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.utils.trigger_rule import TriggerRule
from kubernetes.client import models as k8s

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

# SSM keys for venue-dependent parameters
UNITY_DAPA_CLIENT_ID = "/unity/shared-services/dapa/client-id"
UNITY_DAPA_API_URL = "/unity/shared-services/dapa/api-url"
UNITY_OUTPUT_DATA_BUCKET = "/unity/ds/data/bucket/primary-data-bucket"

# Resources needed by each Task
# EC2 r6a.xlarge	4vCPU	32GiB
CONTAINER_RESOURCES = k8s.V1ResourceRequirements(
    # limits={"memory": "16G", "cpu": "2000m", "ephemeral-storage": "50G"},
    # requests={"memory": "8G", "cpu": "1000m", "ephemeral-storage": "25G"},
    limits={"ephemeral-storage": "50G"},
    requests={"ephemeral-storage": "50G"},
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
    dag_id="sbg_L1_to_L2_e2e_cwl_step_by_step_dag_development",
    description="SBG L1 to L2 End-To-End Workflow as step-by-step CWL DAGs",
    tags=["SBG", "Unity", "SPS", "NASA", "JPL"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=2,
    max_active_tasks=4,
    default_args=dag_default_args,
    params={
        # For step: PREPROCESS
        "preprocess_input_cmr_stac": Param(
            "https://cmr.earthdata.nasa.gov/search/granules.stac"
            "?collection_concept_id=C2408009906-LPCLOUD&"
            "temporal[]=2023-08-10T03:41:03.000Z,2023-08-10T03:41:03.000Z",
            type="string",
        ),
        "preprocess_output_collection_id": Param("urn:nasa:unity:unity:dev:SBG-L1B_PRE___1", type="string"),
        # For step: ISOFIT
        "isofit_input_cmr_collection_name": Param("C2408009906-LPCLOUD", type="string"),
        "isofit_input_cmr_search_start_time": Param("2024-01-03T13:19:36.000Z", type="string"),
        "isofit_input_cmr_search_stop_time": Param("2024-01-03T13:19:36.000Z", type="string"),
        "isofit_input_stac": Param(
            "https://d3vc8w9zcq658.cloudfront.net/am-uds-dapa/collections/"
            "urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/items?"
            "filter=start_datetime%20%3E%3D%20%272024-01-03T13%3A19%3A34Z%27%20AND%20"
            "start_datetime%20%3C%3D%20%272024-01-03T13%3A19%3A36Z%27",
            type="string",
        ),
        "isofit_input_aux_stac": Param(
            '{"numberMatched":{"total_size":1},"numberReturned":1,"stac_version":"1.0.0",'
            '"type":"FeatureCollection",'
            '"links":[{"rel":"self",'
            '"href":"https://d3vc8w9zcq658.cloudfront.net/am-uds-dapa/collections/urn:nasa'
            ':unity:unity:dev:SBG-L1B_PRE___1/items?limit=10"},{"rel":"root",'
            '"href":"https://d3vc8w9zcq658.cloudfront.net"}],"features":[{"type":"Feature",'
            '"stac_version":"1.0.0",'
            '"id":"urn:nasa:unity:unity:dev:SBG-AUX___1:sRTMnet_v120","properties":{'
            '"datetime":"2024-02-14T22:04:41.078000Z","start_datetime":"2024-01-03T13:19:36Z",'
            '"end_datetime":"2024-01-03T13:19:48Z","created":"2024-01-03T13:19:36Z",'
            '"updated":"2024-02-14T22:05:25.248000Z","status":"completed","provider":"unity"},'
            '"geometry":{'
            '"type":"Point","coordinates":[0,0]},"links":[{"rel":"collection","href":"."}],'
            '"assets":{'
            '"sRTMnet_v120.h5":{"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG'
            "-AUX___1/urn:nasa:unity"
            ':unity:dev:SBG-AUX___1:sRTMnet_v120.h5/sRTMnet_v120.h5","title":"sRTMnet_v120.h5",'
            '"description":"size=-1;checksumType=md5;checksum=unknown;","roles":["data"]},'
            '"sRTMnet_v120_aux.npz":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-AUX___1/urn:nasa:unity'
            ":unity:dev:SBG"
            '-AUX___1:sRTMnet_v120.h5/sRTMnet_v120_aux.npz","title":"sRTMnet_v120_aux.npz",'
            '"description":"size=-1;checksumType=md5;checksum=unknown;","roles":["data"]}},'
            '"bbox":[-180,-90,180,90],'
            '"stac_extensions":[],"collection":"urn:nasa:unity:unity:dev:SBG-AUX___1"}]}',
            type="string",
        ),
        "isofit_output_collection_id": Param("urn:nasa:unity:unity:dev:SBG-L2A_RFL___1", type="string"),
        # For step: RESAMPLE
        "resample_input_stac": Param(
            "https://1gp9st60gd.execute-api.us-west-2.amazonaws.com/dev/am-uds-dapa/collections"
            "/urn:nasa:unity:unity"
            ":dev:SBG-L2A_RFL___1/items?filter=start_datetime%20%3E%3D%20%272024-01-03T13%3A19"
            "%3A34Z%27%20AND"
            "%20start_datetime%20%3C%3D%20%272024-01-03T13%3A19%3A36Z%27",
            type="string",
        ),
        "resample_output_collection_id": Param("urn:nasa:unity:unity:dev:SBG-L2A_RSRFL___1", type="string"),
        # For step: REFLECT-CORRECT
        "reflect_correct_input_stac": Param(
            '{"type":"FeatureCollection","features":[{"type":"Feature","stac_version":"1.0.0",'
            '"id":"urn:nasa:unity:unity:dev:SBG-L2A_RSRFL___1'
            ':SISTER_EMIT_L2A_RSRFL_20240103T131936_001",'
            '"properties":{"datetime":"2024-01-03T13:19:36Z",'
            '"start_datetime":"2024-01-03T13:19:36Z",'
            '"end_datetime":"2024-01-03T13:19:48Z","created":"2024-03-04T23:08:10.189899+00:00",'
            '"updated":"2024-03-04T23:08:10.203265Z"},"geometry":null,"links":[{"rel":"root",'
            '"href":"./catalog.json",'
            '"type":"application/json"},{"rel":"parent","href":"./catalog.json",'
            '"type":"application/json"}],'
            '"assets":{"SISTER_EMIT_L2A_RSRFL_20240103T131936_001.bin":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L2A_RSRFL___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L2A_RSRFL___1:SISTER_EMIT_L2A_RSRFL_20240103T131936_001"
            '/SISTER_EMIT_L2A_RSRFL_20240103T131936_001.bin",'
            '"title":"binary file","description":"","roles":["data"]},'
            '"SISTER_EMIT_L2A_RSRFL_20240103T131936_001.hdr":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L2A_RSRFL___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L2A_RSRFL___1:SISTER_EMIT_L2A_RSRFL_20240103T131936_001"
            '/SISTER_EMIT_L2A_RSRFL_20240103T131936_001.hdr",'
            '"title":"header file","description":"","roles":["data"]},'
            '"SISTER_EMIT_L2A_RSRFL_20240103T131936_001_UNC.bin":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L2A_RSRFL___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L2A_RSRFL___1:SISTER_EMIT_L2A_RSRFL_20240103T131936_001"
            "/SISTER_EMIT_L2A_RSRFL_20240103T131936_001_UNC"
            '.bin","title":"binary file","description":"","roles":["data"]},'
            '"SISTER_EMIT_L2A_RSRFL_20240103T131936_001_UNC.hdr":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L2A_RSRFL___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L2A_RSRFL___1:SISTER_EMIT_L2A_RSRFL_20240103T131936_001"
            "/SISTER_EMIT_L2A_RSRFL_20240103T131936_001_UNC"
            '.hdr","title":"header file","description":"","roles":["data"]},'
            '"SISTER_EMIT_L2A_RSRFL_20240103T131936_001.png":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L2A_RSRFL___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L2A_RSRFL___1:SISTER_EMIT_L2A_RSRFL_20240103T131936_001"
            '/SISTER_EMIT_L2A_RSRFL_20240103T131936_001.png",'
            '"title":"image/png file","description":"","roles":["browse"]},'
            '"SISTER_EMIT_L2A_RSRFL_20240103T131936_001.json":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L2A_RSRFL___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L2A_RSRFL___1:SISTER_EMIT_L2A_RSRFL_20240103T131936_001"
            "/SISTER_EMIT_L2A_RSRFL_20240103T131936_001.json"
            '","title":"text/json file","description":"","roles":["metadata"]}},'
            '"stac_extensions":[],'
            '"collection":"urn:nasa:unity:unity:dev:SBG-L2A_RSRFL___1"},{"type":"Feature",'
            '"stac_version":"1.0.0",'
            '"id":"urn:nasa:unity:unity:dev:SBG-L1B_PRE___1'
            ':SISTER_EMIT_L1B_RDN_20240103T131936_001","properties":{'
            '"datetime":"2024-01-03T13:19:36Z","start_datetime":"2024-01-03T13:19:36Z",'
            '"end_datetime":"2024-01-03T13:19:48Z","created":"2024-03-04T22:50:20.726229+00:00",'
            '"updated":"2024-03-04T22:50:20.726712Z"},"geometry":null,"links":[{"rel":"root",'
            '"href":"./catalog.json",'
            '"type":"application/json"},{"rel":"parent","href":"./catalog.json",'
            '"type":"application/json"}],'
            '"assets":{"SISTER_EMIT_L1B_RDN_20240103T131936_001.bin":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L1B_PRE___1:SISTER_EMIT_L1B_RDN_20240103T131936_001"
            '/SISTER_EMIT_L1B_RDN_20240103T131936_001.bin",'
            '"title":"binary file","description":"","roles":["data"]},'
            '"SISTER_EMIT_L1B_RDN_20240103T131936_001.hdr":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L1B_PRE___1:SISTER_EMIT_L1B_RDN_20240103T131936_001"
            '/SISTER_EMIT_L1B_RDN_20240103T131936_001.hdr",'
            '"title":"None file","description":"","roles":["metadata"]},'
            '"SISTER_EMIT_L1B_RDN_20240103T131936_001_LOC.bin":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L1B_PRE___1:SISTER_EMIT_L1B_RDN_20240103T131936_001"
            '/SISTER_EMIT_L1B_RDN_20240103T131936_001_LOC.bin",'
            '"title":"binary file","description":"","roles":["data"]},'
            '"SISTER_EMIT_L1B_RDN_20240103T131936_001_LOC.hdr":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L1B_PRE___1:SISTER_EMIT_L1B_RDN_20240103T131936_001"
            '/SISTER_EMIT_L1B_RDN_20240103T131936_001_LOC.hdr",'
            '"title":"None file","description":"","roles":["metadata"]},'
            '"SISTER_EMIT_L1B_RDN_20240103T131936_001_OBS.bin":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L1B_PRE___1:SISTER_EMIT_L1B_RDN_20240103T131936_001"
            '/SISTER_EMIT_L1B_RDN_20240103T131936_001_OBS.bin",'
            '"title":"binary file","description":"","roles":["data"]},'
            '"SISTER_EMIT_L1B_RDN_20240103T131936_001_OBS.hdr":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L1B_PRE___1:SISTER_EMIT_L1B_RDN_20240103T131936_001"
            '/SISTER_EMIT_L1B_RDN_20240103T131936_001_OBS.hdr",'
            '"title":"None file","description":"","roles":["metadata"]},'
            '"SISTER_EMIT_L1B_RDN_20240103T131936_001.met.json":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L1B_PRE___1:SISTER_EMIT_L1B_RDN_20240103T131936_001"
            '/SISTER_EMIT_L1B_RDN_20240103T131936_001.met.json",'
            '"title":"None file","description":"","roles":["metadata"]},'
            '"SISTER_EMIT_L1B_RDN_20240103T131936_001_LOC.met.json":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L1B_PRE___1:SISTER_EMIT_L1B_RDN_20240103T131936_001"
            "/SISTER_EMIT_L1B_RDN_20240103T131936_001_LOC.met"
            '.json","title":"None file","description":"","roles":["metadata"]},'
            '"SISTER_EMIT_L1B_RDN_20240103T131936_001_OBS.met.json":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L1B_PRE___1:SISTER_EMIT_L1B_RDN_20240103T131936_001"
            "/SISTER_EMIT_L1B_RDN_20240103T131936_001_OBS.met"
            '.json","title":"None file","description":"","roles":["metadata"]},'
            '"SISTER_EMIT_L1B_RDN_20240103T131936_001.png":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L1B_PRE___1:SISTER_EMIT_L1B_RDN_20240103T131936_001"
            '/SISTER_EMIT_L1B_RDN_20240103T131936_001.png",'
            '"title":"image/png file","description":"","roles":["browse"]},'
            '"SISTER_EMIT_L1B_RDN_20240103T131936_001.json":{'
            '"href":"s3://sps-dev-ds-storage/urn:nasa:unity:unity:dev:SBG-L1B_PRE___1/urn:nasa'
            ":unity:unity:dev:SBG"
            "-L1B_PRE___1:SISTER_EMIT_L1B_RDN_20240103T131936_001"
            '/SISTER_EMIT_L1B_RDN_20240103T131936_001.json",'
            '"title":"text/json file","description":"","roles":["metadata"]}},"stac_extensions":[],'
            '"collection":"urn:nasa:unity:unity:dev:SBG-L1B_PRE___1"}]}'
        ),
        "reflect_correct_output_collection_id": Param("urn:nasa:unity:unity:dev:SBG-L2A_CORFL___1"),
        # For step: FRCOVER
        "frcover_input_stac": Param(
            "https://d3vc8w9zcq658.cloudfront.net/am-uds-dapa/collections/urn:nasa:unity:unity"
            ":dev:SBG-L2A_CORFL___1"
            "/items?filter=start_datetime%20%3E%3D%20%272024-01-03T13%3A19%3A34Z%27%20AND"
            "%20start_datetime%20%3C%3D"
            "%20%272024-01-03T13%3A19%3A36Z%27",
            type="string",
        ),
        "frcover_output_collection_id": Param("urn:nasa:unity:unity:dev:SBG-L2B_FRCOV___1", type="string"),
        "frcover_sensor": Param("EMIT", type="string"),
        "frcover_temp_directory": Param("/tmp", type="string"),
        "frcover_experimental": Param("False", type="string"),
        # For all steps
        "crid": Param("001", type="string"),
        # Unity venue-dependent parameters
        # These values should be retrieved from SSM
        # "unity_dapa_client": Param("40c2s0ulbhp9i0fmaph3su9jch", type="string"),
        # "unity_dapa_api": Param("https://d3vc8w9zcq658.cloudfront.net", type="string"),
        "unity_stac_auth": Param("UNITY", type="string"),
        # "output_data_bucket": Param("sps-dev-ds-storage", type="string"),
    },
)


def setup(ti=None, **context):
    """
    Step: Setup
    Task that serializes the job arguments into a JSON string
    """
    # retrieve the venue-dependent parameters from SSM
    ssm_client = boto3.client("ssm", region_name="us-west-2")
    ssm_response = ssm_client.get_parameters(
        Names=[UNITY_DAPA_CLIENT_ID, UNITY_DAPA_API_URL, UNITY_OUTPUT_DATA_BUCKET], WithDecryption=True
    )
    logging.info(ssm_response)

    # dictionary containing venue dependent parameters common to all Tasks
    # this dictionary is merged into each Task specific dictionary
    venue_dict = {}
    for param in ssm_response["Parameters"]:
        if param["Name"] == UNITY_DAPA_CLIENT_ID:
            venue_dict["input_unity_dapa_client"] = param["Value"]
        elif param["Name"] == UNITY_DAPA_API_URL:
            venue_dict["input_unity_dapa_api"] = param["Value"]
        elif param["Name"] == UNITY_OUTPUT_DATA_BUCKET:
            venue_dict["output_data_bucket"] = param["Value"]

    preprocess_dict = {
        "input_processing_labels": INPUT_PROCESSING_LABELS,
        "input_cmr_stac": context["params"]["preprocess_input_cmr_stac"],
        "output_collection_id": context["params"]["preprocess_output_collection_id"],
        "input_crid": context["params"]["crid"],
    }
    preprocess_dict.update(venue_dict)
    ti.xcom_push(key="preprocess_args", value=json.dumps(preprocess_dict))

    isofit_dict = {
        "input_processing_labels": INPUT_PROCESSING_LABELS,
        "input_cmr_collection_name": context["params"]["isofit_input_cmr_collection_name"],
        "input_cmr_search_start_time": context["params"]["isofit_input_cmr_search_start_time"],
        "input_cmr_search_stop_time": context["params"]["isofit_input_cmr_search_stop_time"],
        "input_stac": context["params"]["isofit_input_stac"],
        # Output file from "preprocess" step. Path must be relative to the /scratch directory
        # shared across tasks.
        # "input_stac": {
        #    "class": "File",
        #    "path": "stage_out_results.txt"
        # },
        "input_aux_stac": context["params"]["isofit_input_aux_stac"],
        "output_collection_id": context["params"]["isofit_output_collection_id"],
        "unity_stac_auth": context["params"]["unity_stac_auth"],
        "input_crid": context["params"]["crid"],
    }
    isofit_dict.update(venue_dict)
    ti.xcom_push(key="isofit_args", value=json.dumps(isofit_dict))

    resample_dict = {
        "input_stac": context["params"]["resample_input_stac"],
        "output_resample_collection_id": context["params"]["resample_output_collection_id"],
        "input_crid": context["params"]["crid"],
    }
    resample_dict.update(venue_dict)
    ti.xcom_push(key="resample_args", value=json.dumps(resample_dict))

    reflect_correct_dict = {
        "input_stac": context["params"]["reflect_correct_input_stac"],
        "output_collection_id": context["params"]["reflect_correct_output_collection_id"],
        "input_crid": context["params"]["crid"],
    }
    reflect_correct_dict.update(venue_dict)
    ti.xcom_push(key="reflect_correct_args", value=json.dumps(reflect_correct_dict))

    frcover_dict = {
        # Output file from "reflect-correct" step.
        "input_stac": context["params"]["frcover_input_stac"],
        "output_frcover_collection_id": context["params"]["frcover_output_collection_id"],
        "output_collection": context["params"]["frcover_output_collection_id"],
        "sensor": context["params"]["frcover_sensor"],
        "temp_directory": context["params"]["frcover_temp_directory"],
        "experimental": context["params"]["frcover_experimental"],
        "input_crid": context["params"]["crid"],
        "crid": context["params"]["crid"],
    }
    frcover_dict.update(venue_dict)
    ti.xcom_push(key="frcover_args", value=json.dumps(frcover_dict))


setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)

# Step: PREPROCESS
SBG_PREPROCESS_CWL = (
    "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess" "-workflow.cwl"
)
preprocess_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    name="sbg-preprocess-pod-" + uuid.uuid4().hex,  # unique name for the pod
    task_id="SBG_Preprocess",
    image="ghcr.io/unity-sds/unity-sps/sps-docker-cwl:2.0.0",
    cmds=["/usr/share/cwl/docker_cwl_entrypoint.sh"],
    labels={"task-type": "sbg-task"},
    get_logs=True,
    image_pull_policy="Always",
    service_account_name="airflow-worker",
    restart_policy="Never",
    is_delete_operator_pod=True,  # mapped from on_finish_action to delete succeeded pods
    in_cluster=True,  # Set this if Airflow is running inside a Kubernetes cluster
    host_network=False,
    startup_timeout_seconds=14400,
    arguments=[SBG_PREPROCESS_CWL, "{{ti.xcom_pull(task_ids='Setup', key='preprocess_args')}}"],
    pod_template_file=POD_TEMPLATE_FILE,
    security_context={"privileged": True},
    affinity={
        "nodeAffinity": {
            "preferredDuringSchedulingIgnoredDuringExecution": [
                {
                    "weight": 1,
                    "preference": {
                        "matchExpressions": [
                            {
                                "key": "karpenter.sh/capacity-type",
                                "operator": "In",
                                "values": ["spot"],
                            }
                        ]
                    },
                }
            ],
            "requiredDuringSchedulingIgnoredDuringExecution": {
                "nodeSelectorTerms": [
                    {
                        "matchExpressions": [
                            {
                                "key": "karpenter.k8s.aws/instance-family",
                                "operator": "In",
                                "values": ["c7i", "m7i", "r7i"],
                            },
                            {
                                "key": "karpenter.k8s.aws/instance-cpu",
                                "operator": "In",
                                "values": ["8", "16"],
                            },
                        ]
                    }
                ]
            },
        }
    },
    resources=CONTAINER_RESOURCES,
    priority_weight=1,
    weight_rule="upstream",
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
)

# # Step: ISOFIT
# SBG_ISOFIT_CWL = (
#     "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/isofit/sbg-isofit-workflow.cwl"
# )
# # SBG_ISOFIT_CWL = "https://raw.githubusercontent.com/LucaCinquini/sbg-workflows/devel/isofit/sbg
# # -isofit-workflow.cwl"
# isofit_task = KubernetesPodOperator(
#     namespace=POD_NAMESPACE,
#     name="SBG_Isofit",
#     on_finish_action="delete_succeeded_pod",
#     hostnetwork=False,
#     startup_timeout_seconds=14400,
#     get_logs=True,
#     task_id="SBG_Isofit",
#     full_pod_spec=k8s.V1Pod(k8s.V1ObjectMeta(name="sbg-isofit-pod-" + uuid.uuid4().hex)),
#     pod_template_file=POD_TEMPLATE_FILE,
#     container_resources=CONTAINER_RESOURCES,
#     priority_weight=1,
#     weight_rule="upstream",
#     arguments=[SBG_ISOFIT_CWL, "{{ti.xcom_pull(task_ids='Setup', key='isofit_args')}}"],
#     volume_mounts=[
#         k8s.V1VolumeMount(name="workers-volume", mount_path=WORKING_DIR, sub_path="{{ dag_run.run_id }}")
#     ],
#     volumes=[
#         k8s.V1Volume(
#             name="workers-volume",
#             persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="airflow-kpo"),
#         )
#     ],
#     dag=dag,
# )

# # Step: RESAMPLE
# SBG_RESAMPLE_CWL = (
#     "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/resample/sbg-resample" "-workflow.cwl"
# )
# # SBG_RESAMPLE_ARGS = "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/resample
# # /sbg-resample-workflow
# # .dev.yml"
# resample_task = KubernetesPodOperator(
#     namespace=POD_NAMESPACE,
#     name="SBG_Resample",
#     on_finish_action="delete_succeeded_pod",
#     hostnetwork=False,
#     startup_timeout_seconds=14400,
#     get_logs=True,
#     task_id="SBG_Resample",
#     full_pod_spec=k8s.V1Pod(k8s.V1ObjectMeta(name="sbg-resample-pod-" + uuid.uuid4().hex)),
#     pod_template_file=POD_TEMPLATE_FILE,
#     container_resources=CONTAINER_RESOURCES,
#     priority_weight=1,
#     weight_rule="upstream",
#     arguments=[
#         SBG_RESAMPLE_CWL,
#         # SBG_RESAMPLE_ARGS
#         "{{ti.xcom_pull(task_ids='Setup', key='resample_args')}}",
#     ],
#     volume_mounts=[
#         k8s.V1VolumeMount(name="workers-volume", mount_path=WORKING_DIR, sub_path="{{ dag_run.run_id }}")
#     ],
#     volumes=[
#         k8s.V1Volume(
#             name="workers-volume",
#             persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="airflow-kpo"),
#         )
#     ],
#     dag=dag,
# )

# # Step: REFLECT-CORRECT
# SBG_REFLECT_CORRECT_CWL = (
#     "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/reflect-correct/sbg-reflect"
#     "-correct-workflow.cwl"
# )
# reflect_correct_task = KubernetesPodOperator(
#     namespace=POD_NAMESPACE,
#     name="SBG_Reflect_Correct",
#     on_finish_action="delete_succeeded_pod",
#     hostnetwork=False,
#     startup_timeout_seconds=14400,
#     get_logs=True,
#     task_id="SBG_Reflect_Correct",
#     full_pod_spec=k8s.V1Pod(k8s.V1ObjectMeta(name="sbg-reflect-correct-pod-" + uuid.uuid4().hex)),
#     pod_template_file=POD_TEMPLATE_FILE,
#     container_resources=CONTAINER_RESOURCES,
#     priority_weight=1,
#     weight_rule="upstream",
#     arguments=[
#         SBG_REFLECT_CORRECT_CWL,
#         # SBG_REFLECT_CORRECT_ARGS
#         "{{ti.xcom_pull(task_ids='Setup', key='reflect_correct_args')}}",
#     ],
#     volume_mounts=[
#         k8s.V1VolumeMount(name="workers-volume", mount_path=WORKING_DIR, sub_path="{{ dag_run.run_id }}")
#     ],
#     volumes=[
#         k8s.V1Volume(
#             name="workers-volume",
#             persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="airflow-kpo"),
#         )
#     ],
#     dag=dag,
# )

# # Step: FRCOVER
# SBG_FRCOVER_CWL = (
#     "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/frcover/sbg-frcover-workflow" ".cwl"
# )
# # SBG_FRCOVER_ARGS = "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/frcover/sbg
# # -frcover-workflow.dev
# # .yml"
# frcover_task = KubernetesPodOperator(
#     namespace=POD_NAMESPACE,
#     name="SBG_Frcover",
#     on_finish_action="delete_succeeded_pod",
#     hostnetwork=False,
#     startup_timeout_seconds=14400,
#     get_logs=True,
#     task_id="SBG_Frcover",
#     full_pod_spec=k8s.V1Pod(k8s.V1ObjectMeta(name="sbg-frcover-pod-" + uuid.uuid4().hex)),
#     pod_template_file=POD_TEMPLATE_FILE,
#     container_resources=CONTAINER_RESOURCES,
#     priority_weight=1,
#     weight_rule="upstream",
#     arguments=[
#         SBG_FRCOVER_CWL,
#         # SBG_FRCOVER_ARGS
#         "{{ti.xcom_pull(task_ids='Setup', key='frcover_args')}}",
#     ],
#     volume_mounts=[
#         k8s.V1VolumeMount(name="workers-volume", mount_path=WORKING_DIR, sub_path="{{ dag_run.run_id }}")
#     ],
#     volumes=[
#         k8s.V1Volume(
#             name="workers-volume",
#             persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="airflow-kpo"),
#         )
#     ],
#     dag=dag,
# )


def cleanup(**context):
    """
    Tasks that deletes all data shared between Tasks
    from the Kubernetes PersistentVolume
    """
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
    trigger_rule=TriggerRule.ALL_DONE,
    # priority_weight=1,
    # weight_rule="upstream",
    dag=dag,
)

# setup_task >> preprocess_task >> isofit_task >> resample_task >> reflect_correct_task >>
# frcover_task >> cleanup_task

chain(
    setup_task,
    preprocess_task,
    # [isofit_task, reflect_correct_task],
    # [resample_task, frcover_task],
    cleanup_task,
)
