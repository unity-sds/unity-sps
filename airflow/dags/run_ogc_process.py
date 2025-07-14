"""
DAG with two separate tasks to submit a job to an OGC-compliant process API
and then monitor its status.
"""
import json
import logging
from datetime import datetime

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.models.baseoperator import chain
from airflow.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.providers.cncf.kubernetes.secret import Secret as AirflowK8sSecret
from airflow.utils.trigger_rule import TriggerRule
from kubernetes.client import models as k8s

# --- Configuration Constants ---

# The name of the Kubernetes secret that holds the PGT token.
K8S_SECRET_NAME = "pgt-token-secret"
K8S_SECRET_KEY = "pgt-token"
TOKEN_ENV_VAR = "PGT_TOKEN"

# The base URL for the OGC Process API.
API_BASE_URL = "https://api.dit.maap-project.org/api/ogc"

# The Kubernetes namespace where the pods will run.
POD_NAMESPACE = "airflow"  # Change this to your Airflow namespace

# A lightweight Docker image with curl and jq for making API requests.
DOCKER_IMAGE = "stedolan/jq@sha256:36519247696232f7a09d3a0e6653131093c7deda36f8a4e34a70b09f19e42e61"

# Define the secret to be mounted as an environment variable.
secret_env_vars = [
    AirflowK8sSecret(
        deploy_type="env",
        deploy_target=TOKEN_ENV_VAR,
        secret=K8S_SECRET_NAME,
        key=K8S_SECRET_KEY,
    )
]

# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
}

# --- DAG Definition ---

dag = DAG(
    dag_id="ogc_two_task_job_runner",
    description="Submits and monitors an OGC job in two separate tasks.",
    dag_display_name="OGC Two-Task Job Runner",
    tags=["ogc", "api", "maap", "kubernetes"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=10,
    default_args=dag_default_args,
    params={
        "process_id": Param(
            "test-process",
            type="string",
            title="Process ID",
            description="The identifier of the OGC process to execute.",
        ),
        "job_inputs": Param(
            json.dumps(
                {
                    "queue": "maap-dps-sandbox",
                    "inputs": {},
                }
            ),
            type="string",
            title="Job Inputs (JSON string)",
            description="A JSON string representing the inputs payload for the job.",
        ),
    },
)

# --- Task Definitions ---

def setup(**context):
    """A simple setup task to log parameters."""
    logging.info("Starting OGC job submission and monitoring DAG.")
    logging.info(f"Parameters received: {context['params']}")

setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)

# This shell command submits the job and writes the jobID to a special file
# that Airflow uses for XComs.
submit_command = [
    "/bin/sh",
    "-c",
    f"""
        set -e
        echo "Submitting job for process: {{ params.process_id }}"
        
        SUBMIT_URL="{API_BASE_URL}/processes/{{ params.process_id }}/execution"
        
        # The payload is now passed as a templated argument
        PAYLOAD='{{ params.job_inputs }}'
        
        # Make the request and extract jobID
        response=$(curl -s -f -X POST "$SUBMIT_URL" \\
            -H "Authorization: Bearer ${TOKEN_ENV_VAR}" \\
            -H "Content-Type: application/json" \\
            -d "$PAYLOAD")
        
        echo "API Response: $response"
        job_id=$(echo "$response" | jq -r .jobID)
        
        if [ "$job_id" = "null" ] || [ -z "$job_id" ]; then
            echo "Failed to get jobID from response."
            exit 1
        fi
        
        echo "Job submitted successfully. Job ID: $job_id"
        
        # Write the job_id to the XCom return file for the next task
        # The value MUST be JSON-parsable, so we quote it.
        echo -n "\\"\\"{job_id}\\"\\"" > /airflow/xcom/return.json
    """,
]

submit_job_task = KubernetesPodOperator(
    task_id="submit_job_task",
    namespace=POD_NAMESPACE,
    image=DOCKER_IMAGE,
    name="ogc-submit-pod",
    cmds=submit_command,
    secrets=secret_env_vars,
    in_cluster=True,
    get_logs=True,
    # This is crucial for enabling XCom push from the pod
    do_xcom_push=True,
    dag=dag,
)

# This shell command polls for job status. The jobID is passed in as an argument.
monitor_command = [
    "/bin/sh",
    "-c",
    """
        set -e
        job_id="$1" # The jobID is the first argument
        if [ -z "$job_id" ]; then
            echo "job_id argument not provided."
            exit 1
        fi
        
        echo "Starting to monitor job ID: $job_id"
        STATUS_URL="${API_BASE_URL}/jobs/$job_id"
        
        TIMEOUT=3600
        POLL_INTERVAL=30
        SECONDS=0
        
        while [ $SECONDS -lt $TIMEOUT ]; do
            echo "Checking status..."
            response=$(curl -s -f -H "Authorization: Bearer ${PGT_TOKEN}" "$STATUS_URL")
            status=$(echo "$response" | jq -r .status)
            
            echo "Current status is: $status"
            
            if [ "$status" = "successful" ]; then
                echo "Job completed successfully!"
                exit 0
            elif [ "$status" = "failed" ]; then
                echo "Job failed!"
                echo "Error details: $(echo "$response" | jq .)"
                exit 1
            fi
            
            sleep $POLL_INTERVAL
            SECONDS=$((SECONDS + POLL_INTERVAL))
        done
        
        echo "Job monitoring timed out after $TIMEOUT seconds."
        exit 1
    """,
]

monitor_job_task = KubernetesPodOperator(
    task_id="monitor_job_task",
    namespace=POD_NAMESPACE,
    image=DOCKER_IMAGE,
    name="ogc-monitor-pod",
    cmds=monitor_command,
    # The job_id is pulled from the previous task's XCom return value
    # and passed as the first argument to the monitor_command script.
    arguments=["{{ ti.xcom_pull(task_ids='submit_job_task') }}"],
    secrets=secret_env_vars,
    in_cluster=True,
    get_logs=True,
    dag=dag,
)

def cleanup(**context):
    """A placeholder cleanup task."""
    logging.info("Cleanup executed.")

cleanup_task = PythonOperator(
    task_id="Cleanup", python_callable=cleanup, dag=dag, trigger_rule=TriggerRule.ALL_DONE
)

# Define the task execution chain
chain(setup_task, submit_job_task, monitor_job_task, cleanup_task)
