"""
Script to trigger a DAG.
The current payload is specific to executing the "cwl_dag" for the EMIT workflow.
Syntax: python trigger_dag.py -d <dag_id> -n <num_times>

Example:
export AIRFLOW_HOST=http://emit-dev-httpd-alb-XXXXXXXXXXXX.us-west-2.elb.amazonaws.com:8080/emit/dev/sps/
export AIRFLOW_USERNAME=....
export AIRFLOW_PASSWORD=...
source .venv/bin/activate
python utils/trigger_dag.py -d cwl_dag -n 3
"""

import argparse
import os
import time
from datetime import datetime, timezone
from pprint import pprint

import requests
from requests.auth import HTTPBasicAuth

# EMIT parameters
# cwl_args = '{"stage_in": {"stac_json": "{\\"type\\": \\"FeatureCollection\\", \\"features\\": [{\\"type\\": \\"Feature\\", \\"stac_version\\": \\"1.0.0\\", \\"stac_extensions\\": [\\"https://stac-extensions.github.io/eo/v1.0.0/schema.json\\"], \\"id\\": \\"G2855236155-LPCLOUD\\", \\"geometry\\": {\\"type\\": \\"Polygon\\", \\"coordinates\\": [[[-82.0352783, 41.6404076], [-83.0327911, 41.0799294], [-82.6384277, 40.3780785], [-81.6409149, 40.9385567], [-82.0352783, 41.6404076]]]}, \\"bbox\\": [-83.0327911, 40.3780785, -81.6409149, 41.6404076], \\"properties\\": {\\"datetime\\": \\"2024-02-01T17:41:51Z\\", \\"start_datetime\\": \\"2024-02-01T17:41:51.000Z\\", \\"end_datetime\\": \\"2024-02-01T17:42:03.000Z\\", \\"eo:cloud_cover\\": 31}, \\"links\\": [{\\"rel\\": \\"self\\", \\"href\\": \\"https://cmr.earthdata.nasa.gov:443/search/concepts/G2855236155-LPCLOUD.stac\\"}, {\\"rel\\": \\"parent\\", \\"href\\": \\"https://cmr.earthdata.nasa.gov:443/search/concepts/C2408009906-LPCLOUD.stac\\"}, {\\"rel\\": \\"collection\\", \\"href\\": \\"https://cmr.earthdata.nasa.gov:443/search/concepts/C2408009906-LPCLOUD.stac\\"}, {\\"rel\\": \\"root\\", \\"href\\": \\"https://cmr.earthdata.nasa.gov:443/search/\\"}, {\\"rel\\": \\"via\\", \\"href\\": \\"https://cmr.earthdata.nasa.gov:443/search/concepts/G2855236155-LPCLOUD.json\\"}, {\\"rel\\": \\"via\\", \\"href\\": \\"https://cmr.earthdata.nasa.gov:443/search/concepts/G2855236155-LPCLOUD.umm_json\\"}], \\"assets\\": {\\"metadata\\": {\\"href\\": \\"https://cmr.earthdata.nasa.gov:443/search/concepts/G2855236155-LPCLOUD.xml\\", \\"type\\": \\"application/xml\\"}, \\"browse\\": {\\"href\\": \\"https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-public/EMITL1BRAD.001/EMIT_L1B_RAD_001_20240201T174151_2403212_032/EMIT_L1B_RAD_001_20240201T174151_2403212_032.png\\", \\"type\\": \\"image/png\\", \\"title\\": \\"Download EMIT_L1B_RAD_001_20240201T174151_2403212_032.png\\"}, \\"opendap\\": {\\"href\\": \\"https://opendap.earthdata.nasa.gov/collections/C2408009906-LPCLOUD/granules/EMIT_L1B_RAD_001_20240201T174151_2403212_032\\", \\"title\\": \\"OPeNDAP request URL\\"}, \\"data\\": {\\"href\\": \\"https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/EMITL1BRAD.001/EMIT_L1B_RAD_001_20240201T174151_2403212_032/EMIT_L1B_RAD_001_20240201T174151_2403212_032.nc\\", \\"title\\": \\"Download EMIT_L1B_RAD_001_20240201T174151_2403212_032.nc\\"}, \\"data1\\": {\\"href\\": \\"https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/EMITL1BRAD.001/EMIT_L1B_RAD_001_20240201T174151_2403212_032/EMIT_L1B_OBS_001_20240201T174151_2403212_032.nc\\", \\"title\\": \\"Download EMIT_L1B_OBS_001_20240201T174151_2403212_032.nc\\"}}, \\"collection\\": \\"C2408009906-LPCLOUD\\"}, {\\"type\\": \\"Feature\\", \\"stac_version\\": \\"1.0.0\\", \\"stac_extensions\\": [\\"https://stac-extensions.github.io/eo/v1.0.0/schema.json\\"], \\"id\\": \\"G2855238895-LPCLOUD\\", \\"geometry\\": {\\"type\\": \\"Polygon\\", \\"coordinates\\": [[[-82.0352783, 41.6404076], [-83.0327911, 41.0799294], [-82.6384277, 40.3780785], [-81.6409149, 40.9385567], [-82.0352783, 41.6404076]]]}, \\"bbox\\": [-83.0327911, 40.3780785, -81.6409149, 41.6404076], \\"properties\\": {\\"datetime\\": \\"2024-02-01T17:41:51Z\\", \\"start_datetime\\": \\"2024-02-01T17:41:51.000Z\\", \\"end_datetime\\": \\"2024-02-01T17:42:03.000Z\\", \\"eo:cloud_cover\\": 31}, \\"links\\": [{\\"rel\\": \\"self\\", \\"href\\": \\"https://cmr.earthdata.nasa.gov:443/search/concepts/G2855238895-LPCLOUD.stac\\"}, {\\"rel\\": \\"parent\\", \\"href\\": \\"https://cmr.earthdata.nasa.gov:443/search/concepts/C2408750690-LPCLOUD.stac\\"}, {\\"rel\\": \\"collection\\", \\"href\\": \\"https://cmr.earthdata.nasa.gov:443/search/concepts/C2408750690-LPCLOUD.stac\\"}, {\\"rel\\": \\"root\\", \\"href\\": \\"https://cmr.earthdata.nasa.gov:443/search/\\"}, {\\"rel\\": \\"via\\", \\"href\\": \\"https://cmr.earthdata.nasa.gov:443/search/concepts/G2855238895-LPCLOUD.json\\"}, {\\"rel\\": \\"via\\", \\"href\\": \\"https://cmr.earthdata.nasa.gov:443/search/concepts/G2855238895-LPCLOUD.umm_json\\"}], \\"assets\\": {\\"metadata\\": {\\"href\\": \\"https://cmr.earthdata.nasa.gov:443/search/concepts/G2855238895-LPCLOUD.xml\\", \\"type\\": \\"application/xml\\"}, \\"browse\\": {\\"href\\": \\"https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-public/EMITL2ARFL.001/EMIT_L2A_RFL_001_20240201T174151_2403212_032/EMIT_L2A_RFL_001_20240201T174151_2403212_032.png\\", \\"type\\": \\"image/png\\", \\"title\\": \\"Download EMIT_L2A_RFL_001_20240201T174151_2403212_032.png\\"}, \\"opendap\\": {\\"href\\": \\"https://opendap.earthdata.nasa.gov/collections/C2408750690-LPCLOUD/granules/EMIT_L2A_RFL_001_20240201T174151_2403212_032\\", \\"title\\": \\"OPeNDAP request URL\\"}, \\"data\\": {\\"href\\": \\"https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/EMITL2ARFL.001/EMIT_L2A_RFL_001_20240201T174151_2403212_032/EMIT_L2A_RFL_001_20240201T174151_2403212_032.nc\\", \\"title\\": \\"Download EMIT_L2A_RFL_001_20240201T174151_2403212_032.nc\\"}, \\"data1\\": {\\"href\\": \\"https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/EMITL2ARFL.001/EMIT_L2A_RFL_001_20240201T174151_2403212_032/EMIT_L2A_RFLUNCERT_001_20240201T174151_2403212_032.nc\\", \\"title\\": \\"Download EMIT_L2A_RFLUNCERT_001_20240201T174151_2403212_032.nc\\"}, \\"data2\\": {\\"href\\": \\"https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/EMITL2ARFL.001/EMIT_L2A_RFL_001_20240201T174151_2403212_032/EMIT_L2A_MASK_001_20240201T174151_2403212_032.nc\\", \\"title\\": \\"Download EMIT_L2A_MASK_001_20240201T174151_2403212_032.nc\\"}}, \\"collection\\": \\"C2408750690-LPCLOUD\\"}]}", "downloading_roles": "", "downloading_keys": "data, data1, data2", "download_type": "DAAC", "edl_username": "/sps/processing/workflows/edl_username", "edl_password_type": "PARAM_STORE", "edl_password": "/sps/processing/workflows/edl_password", "unity_client_id": "", "unity_stac_auth": "NONE"}, "parameters": {"output_collection": "urn:nasa:unity:emit:dev:emit_ghg_test___1"}, "stage_out": {"staging_bucket": "emit-dev-unity-data", "collection_id": "urn:nasa:unity:emit:dev:emit_ghg_test___1", "result_path_prefix": "stage_out"}}'
# cwl_workflow = "http://awslbdockstorestack-lb-1429770210.us-west-2.elb.amazonaws.com:9998/api/ga4gh/trs/v2/tools/%23workflow%2Fdockstore.org%2Fedwinsarkissian%2Femit-ghg_test/versions/29/PLAIN-CWL/descriptor/%2Fworkflow.cwl"
# cwl_workflow = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/main/emit/GodwinShen/workflow.cwl"
# cwl_args = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/main/emit/GodwinShen/emit-ghg-dev.json"
# ec2_instance_type = "r7i.xlarge"

cwl_workflow = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/main/demos/echo_message.cwl"
cwl_args = '{"message": "Hello Unity"}'
ec2_instance_type = "t3.medium"


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dag", help="ID of DAG to run", type=str)
    parser.add_argument("-n", "--num", help="Number of DAG runs", type=int, default=1)
    args = parser.parse_args()
    dag = args.dag
    num = args.num

    # get airflow host,user,pwd from ENV variables
    airflow_host = os.getenv("AIRFLOW_HOST")
    airflow_username = os.getenv("AIRFLOW_USERNAME")
    airflow_password = os.getenv("AIRFLOW_PASSWORD")

    url = f"{airflow_host}/api/v1/dags/{dag}/dagRuns"
    headers = {"Content-type": "application/json", "Accept": "text/json"}

    for i in range(num):
        dt_now = datetime.now(timezone.utc)
        logical_date = dt_now.strftime("%Y-%m-%dT%H:%M:%SZ")
        # data = {"logical_date": logical_date}
        # Example on how to pass DAG specific parameters
        data = {
            "logical_date": logical_date,
            "conf": {
                "cwl_args": cwl_args,
                "cwl_workflow": cwl_workflow,
                "request_instance_type": ec2_instance_type,
                "request_storage": "50Gi",
            },
        }
        result = requests.post(
            url, json=data, headers=headers, auth=HTTPBasicAuth(airflow_username, airflow_password)
        )
        result_json = result.json()
        pprint(result_json)
        time.sleep(1)


if __name__ == "__main__":
    main()
