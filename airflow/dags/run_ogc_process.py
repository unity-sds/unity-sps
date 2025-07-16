"""
DAG with two separate tasks to submit a job to an OGC-compliant process API
and then monitor its status.
"""
import json
import logging
from datetime import datetime
import os

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.models.baseoperator import chain
from airflow.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.providers.cncf.kubernetes.secret import Secret as AirflowK8sSecret
from airflow.utils.trigger_rule import TriggerRule
from kubernetes.client import models as k8s
from unity_sps_utils import (
    DEFAULT_LOG_LEVEL,
    EC2_TYPES,
    NODE_POOL_DEFAULT,
    NODE_POOL_HIGH_WORKLOAD,
    POD_LABEL,
    POD_NAMESPACE,
    build_ec2_type_label,
    get_affinity,
)
from airflow.operators.python import PythonOperator, get_current_context

# --- Configuration Constants ---

K8S_SECRET_NAME = "sps-app-credentials"
LOG_LEVEL_TYPE = {10: "DEBUG", 20: "INFO"}

DOCKER_IMAGE_SUBMIT_JOB = "jplmdps/ogc-job-runner:latest"

# Define the secret to be mounted as an environment variable.
secret_env_vars = [
    AirflowK8sSecret(
        deploy_type="env",
        deploy_target="MAAP_PGT",
        secret=K8S_SECRET_NAME,
        key="MAAP_PGT",
    )
]

# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}

submit_job_env_vars = [
    k8s.V1EnvVar(
        name="SUBMIT_JOB_URL",
        value="https://api.dit.maap-project.org/api/ogc/processes/{process_id}/execution",
    ),
    k8s.V1EnvVar(name="PROCESS_ID", value="{{ params.process_id }}"),
    k8s.V1EnvVar(name="JOB_INPUTS", value="{{ params.job_inputs }}"),
    k8s.V1EnvVar(name="SUBMIT_JOB", value="true")
]

monitor_job_env_vars = [
    k8s.V1EnvVar(
        name="MONITOR_JOB_URL",
        value="https://api.dit.maap-project.org/api/ogc/jobs/{job_id}",
    ),
    k8s.V1EnvVar(name="JOB_ID", value="{{ ti.xcom_pull(task_ids='submit_job_task', key='return_value')['job_id'] }}"),
    k8s.V1EnvVar(name="SUBMIT_JOB", value="false")
]

# --- DAG Definition ---

dag = DAG(
    dag_id="run_ogc_process",
    description="Submits a job to an OGC process and monitors",
    dag_display_name="Run an OGC Process",
    tags=["ogc", "job"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=10,
    default_args=dag_default_args,
    params={
        "process_id": Param(
            type="integer",
            title="Process ID",
            description="The numerical identifier of the OGC process to execute.",
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
        "log_level": Param(
            DEFAULT_LOG_LEVEL,
            type="integer",
            enum=list(LOG_LEVEL_TYPE.keys()),
            values_display={key: f"{key} ({value})" for key, value in LOG_LEVEL_TYPE.items()},
            title="Processing log levels",
            description=("Log level for DAG processing"),
        ),
        "request_instance_type": Param(
            "t3.medium",
            type="string",
            enum=list(EC2_TYPES.keys()),
            values_display={key: f"{build_ec2_type_label(key)}" for key in EC2_TYPES.keys()},
            title="EC2 instance type",
        ),
        "request_storage": Param(
            "10Gi", type="string", enum=["10Gi", "50Gi", "100Gi", "150Gi", "200Gi", "250Gi"]
        ),
        "use_ecr": Param(False, type="boolean", title="Log into AWS Elastic Container Registry (ECR)"),
    },
)

# --- Task Definitions ---

def setup(ti=None,**context):
    """Task that selects the proper Karpenter Node Pool depending on the user requested resources."""

    logging.info("Starting OGC job submission and monitoring DAG.")
    logging.info(f"Parameters received: {context['params']}")
    context = get_current_context()
    logging.info(f"DAG Run parameters: {json.dumps(context['params'], sort_keys=True, indent=4)}")

    # select the node pool based on what resources were requested
    node_pool = NODE_POOL_DEFAULT
    storage = context["params"]["request_storage"]  # 100Gi
    container_storage = int(storage[0:-2])  # 100
    ti.xcom_push(key="container_storage", value=container_storage)

    # from "t3.large (General Purpose: 2vCPU, 8GiB)" to "t3.large"
    instance_type = context["params"]["request_instance_type"]
    cpu = EC2_TYPES[instance_type]["cpu"]
    memory = EC2_TYPES[instance_type]["memory"]
    ti.xcom_push(key="instance_type", value=instance_type)
    logging.info(f"Requesting EC2 instance type={instance_type}")

    logging.info(f"Requesting container storage={container_storage}Gi")
    if (container_storage > 30) or (cpu > 16) or (memory > 32):
        node_pool = NODE_POOL_HIGH_WORKLOAD
    logging.info(f"Selecting node pool={node_pool}")
    ti.xcom_push(key="node_pool", value=node_pool)

    # select "use_ecr" argument and determine if ECR login is required
    logging.info("Use ECR: %s", context["params"]["use_ecr"])
    if context["params"]["use_ecr"]:
        ecr_login = os.environ["AIRFLOW_VAR_ECR_URI"]
        ti.xcom_push(key="ecr_login", value=ecr_login)
        logging.info("ECR login: %s", ecr_login)

    # select log level based on debug
    logging.info(f"Selecting log level: {context['params']['log_level']}.")

setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)

submit_job_task = KubernetesPodOperator(
    task_id="submit_job_task",
    namespace=POD_NAMESPACE,
    image=DOCKER_IMAGE_SUBMIT_JOB,
    name="ogc-submit-pod",
    env_vars=submit_job_env_vars,
    secrets=secret_env_vars,
    service_account_name="airflow-worker",
    in_cluster=True,
    get_logs=True,
    startup_timeout_seconds=600,
    container_security_context={"privileged": True},
    container_resources=k8s.V1ResourceRequirements(
        requests={
            "ephemeral-storage": "{{ti.xcom_pull(task_ids='Setup', key='container_storage')}}",
        },
    ),
    container_logs=True,
    do_xcom_push=True,
    dag=dag,
    node_selector={
        "karpenter.sh/nodepool": "{{ti.xcom_pull(task_ids='Setup', key='node_pool')}}",
        "node.kubernetes.io/instance-type": "{{ti.xcom_pull(task_ids='Setup', key='instance_type')}}",
    },
    labels={"pod": POD_LABEL},
    annotations={"karpenter.sh/do-not-disrupt": "true"},
    # note: 'affinity' cannot yet be templated
    affinity=get_affinity(
        capacity_type=["spot"],
        anti_affinity_label=POD_LABEL,
    ),
    on_finish_action="keep_pod",
    is_delete_operator_pod=False,
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
    image=DOCKER_IMAGE_SUBMIT_JOB,
    name="ogc-monitor-pod",
    env_vars=monitor_job_env_vars,
    secrets=secret_env_vars,
    service_account_name="airflow-worker",
    in_cluster=True,
    get_logs=True,
    startup_timeout_seconds=600,
    container_security_context={"privileged": True},
    container_resources=k8s.V1ResourceRequirements(
        requests={
            "ephemeral-storage": "{{ti.xcom_pull(task_ids='Setup', key='container_storage')}}",
        },
    ),
    container_logs=True,
    dag=dag,
    node_selector={
        "karpenter.sh/nodepool": "{{ti.xcom_pull(task_ids='Setup', key='node_pool')}}",
        "node.kubernetes.io/instance-type": "{{ti.xcom_pull(task_ids='Setup', key='instance_type')}}",
    },
    labels={"pod": POD_LABEL},
    annotations={"karpenter.sh/do-not-disrupt": "true"},
    # note: 'affinity' cannot yet be templated
    affinity=get_affinity(
        capacity_type=["spot"],
        anti_affinity_label=POD_LABEL,
    ),
    on_finish_action="keep_pod",
    is_delete_operator_pod=False,
)

# monitor_job_task = KubernetesPodOperator(
#     task_id="monitor_job_task",
#     namespace=POD_NAMESPACE,
#     image=DOCKER_IMAGE,
#     name="ogc-monitor-pod",
#     cmds=monitor_command,
#     # The job_id is pulled from the previous task's XCom return value
#     # and passed as the first argument to the monitor_command script.
#     arguments=["{{ ti.xcom_pull(task_ids='submit_job_task') }}"],
#     secrets=secret_env_vars,
#     in_cluster=True,
#     get_logs=True,
#     dag=dag,
# )

def cleanup(**context):
    """A placeholder cleanup task."""
    logging.info("Cleanup executed.")

cleanup_task = PythonOperator(
    task_id="Cleanup", python_callable=cleanup, dag=dag, trigger_rule=TriggerRule.ALL_DONE
)

#chain(setup_task, submit_job_task, cleanup_task)
chain(setup_task, submit_job_task, monitor_job_task, cleanup_task)
