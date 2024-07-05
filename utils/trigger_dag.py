"""
Script to trigger a DAG
Syntax: python trigger_dag.py -d <dag_id> -n <num_times>

Example:
export AIRFLOW_HOST=http://k8s-airflow-airflowi-004fdefd11-514392646.us-west-2.elb.amazonaws.com:5000
export AIRFLOW_USERNAME=....
export AIRFLOW_PASSWORD=...
source .venv/bin/activate
python utils/trigger_dag.py -d busybox -n 1
"""

import argparse
import os
import time
from datetime import datetime, timezone
from pprint import pprint

import requests
from requests.auth import HTTPBasicAuth


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
        data = {"logical_date": logical_date}
        # Example on how to pass DAG specific parameters
        # data = {"logical_date": logical_date,
        #        "conf": {"cwl_args": "abc123"}
        #       }
        result = requests.post(
            url, json=data, headers=headers, auth=HTTPBasicAuth(airflow_username, airflow_password)
        )
        result_json = result.json()
        pprint(result_json)
        time.sleep(1)


if __name__ == "__main__":
    main()
