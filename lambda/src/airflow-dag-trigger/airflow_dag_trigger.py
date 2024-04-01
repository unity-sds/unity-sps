import logging
import os
import uuid
from datetime import datetime
from typing import List
from urllib.parse import unquote_plus

import requests
from aws_lambda_powertools.utilities.parser import envelopes, event_parser
from aws_lambda_powertools.utilities.parser.models import S3Model
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AIRFLOW_BASE_API_ENDPOINT = os.environ.get("AIRFLOW_BASE_API_ENDPOINT")
AIRFLOW_USERNAME = os.environ.get("AIRFLOW_USERNAME")
AIRFLOW_PASSWORD = os.environ.get("AIRFLOW_PASSWORD")


def trigger_airflow_dag(dag_id: str):
    url = f"{AIRFLOW_BASE_API_ENDPOINT}/dags/{dag_id}/dagRuns"
    dag_run_id = str(uuid.uuid4())
    logical_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    auth = (AIRFLOW_USERNAME, AIRFLOW_PASSWORD)
    payload = {"dag_run_id": dag_run_id, "logical_date": logical_date, "conf": {}, "note": ""}
    response = requests.post(url, auth=auth, headers=headers, json=payload)
    if response.status_code == 200 or response.status_code == 201:
        logger.info(f"Successfully triggered Airflow DAG {dag_id}: {response.json()}")
    else:
        logger.error(f"Failed to trigger Airflow DAG {dag_id}: {response.text}")


@event_parser(model=S3Model, envelope=envelopes.SnsSqsEnvelope)
def lambda_handler(event: List[S3Model], context: LambdaContext) -> dict:
    try:
        object_key = unquote_plus(event[0].Records[0].s3.object.key)
        bucket_name = unquote_plus(event[0].Records[0].s3.bucket.name)
        logger.info(f"Source bucket: {bucket_name}, Source key: {object_key}")
        dag_id = "sbg-l1-to-l2-e2e-cwl-step-by-step-dag"
        trigger_airflow_dag(dag_id)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return {"statusCode": 500, "body": "An unexpected error occurred: " + str(e)}

    return {"statusCode": 200, "body": "Success!"}
