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

# EMIT parameters (using DickerHub)
# cwl_workflow = "http://awslbdockstorestack-lb-1429770210.us-west-2.elb.amazonaws.com:9998/api/ga4gh/trs/v2/tools/%23workflow%2Fdockstore.org%2FGodwinShen%2Femit-ghg/versions/9/plain-CWL/descriptor/workflow.cwl"
# cwl_args = "https://raw.githubusercontent.com/GodwinShen/emit-ghg/refs/heads/main/test/emit-ghg-dev.json"
# EMIT parameters (using ECR)
cwl_workflow = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/main/emit/GodwinShen/workflow.cwl"
cwl_args = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/main/emit/GodwinShen/emit-ghg-dev.json"
request_storage = "100Gi"
ec2_instance_type = "r7i.2xlarge"
use_ecr = True

# cwl_workflow = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/main/demos/echo_message.cwl"
# cwl_args = '{"message": "Hello Unity"}'
# ec2_instance_type = "t3.medium"
# request_storage = "10Gi"


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
                "request_storage": request_storage,
                "use_ecr": use_ecr,
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
