"""
DAG with two separate tasks to submit a job to an OGC-compliant process API
and then monitor its status.
"""
import json
import logging
from datetime import datetime
import os
import requests
import re

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

def fetch_ogc_processes():
    """Fetch available processes from the OGC API and create mapping."""
    try:
        response = requests.get("https://api.dit.maap-project.org/api/ogc/processes", timeout=30)
        response.raise_for_status()
        
        processes_data = response.json()
        process_mapping = {}
        dropdown_options = []
        
        for process in processes_data.get("processes", []):
            process_id = process.get("id")
            process_version = process.get("version")
            
            # Extract numerical ID from links
            numerical_id = None
            for link in process.get("links", []):
                if link.get("rel") == "self":
                    href = link.get("href", "")
                    # Extract number from href like "/ogc/processes/7"
                    match = re.search(r'/processes/(\d+)$', href)
                    if match:
                        numerical_id = int(match.group(1))
                        break
            
            if process_id and numerical_id:
                display_name = f"{process_id}:{process_version}"
                dropdown_options.append(display_name)
                process_mapping[display_name] = numerical_id
        
        return process_mapping, dropdown_options
        
    except requests.RequestException as e:
        logging.error(f"Failed to fetch processes: {e}")
        # Return fallback mapping
        return {"example-process:1.0": 1}, ["example-process:1.0"]
    except Exception as e:
        logging.error(f"Error processing OGC processes: {e}")
        return {"example-process:1.0": 1}, ["example-process:1.0"]

K8S_SECRET_NAME = "sps-app-credentials"
LOG_LEVEL_TYPE = {10: "DEBUG", 20: "INFO"}
PROCESS_MAPPING, DROPDOWN_OPTIONS = fetch_ogc_processes()

DOCKER_IMAGE = "jplmdps/ogc-job-runner:latest"

secret_env_vars = [
    AirflowK8sSecret(
        deploy_type="env",
        deploy_target="MAAP_PGT",
        secret=K8S_SECRET_NAME,
        key="MAAP_PGT",
    )
]

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
    k8s.V1EnvVar(name="PROCESS_ID", value="{{ ti.xcom_pull(task_ids='Setup', key='return_value')['numerical_process_id'] }}"),
    k8s.V1EnvVar(name="JOB_INPUTS", value="{{ params.job_inputs }}"),
    k8s.V1EnvVar(name="QUEUE", value="{{ params.queue }}"),
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
    dag_id="run_ogc_process2",
    description="Submits a job to an OGC process and monitors",
    dag_display_name="Run an OGC Process2",
    tags=["ogc", "job"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=10,
    default_args=dag_default_args,
    params={
        "selected_process": Param(
            default=DROPDOWN_OPTIONS[0] if DROPDOWN_OPTIONS else "example-process:1.0",
            enum=DROPDOWN_OPTIONS,
            title="Process Selection",
            description=f"Select a process to execute. Available processes: {', '.join(DROPDOWN_OPTIONS)}",
        ),
        "queue": Param(
            "maap-dps-sandbox",
            type="string",
            title="Queue",
            description="The MAAP queue to submit the job to",
        ),
        "job_inputs": Param(
            {},
            type="string",
            title="Job Inputs",
            description="A JSON string representing the inputs payload for the job.",
        )
    },
)

# --- Task Definitions ---
def setup(ti=None, **context):
    """Task that logs DAG parameters and process mapping information."""
    
    logging.info("Starting OGC job submission and monitoring DAG (Dynamic Version).")
    logging.info(f"Parameters received: {context['params']}")
    logging.info(f"Available processes: {len(DROPDOWN_OPTIONS)}")
    logging.info(f"Process mapping: {json.dumps(PROCESS_MAPPING, indent=2)}")
    
    context = get_current_context()
    logging.info(f"DAG Run parameters: {json.dumps(context['params'], sort_keys=True, indent=4)}")
    
    selected_process = context['params'].get('selected_process')
    if selected_process in PROCESS_MAPPING:
        numerical_id = PROCESS_MAPPING[selected_process]
        logging.info(f"Selected process '{selected_process}' maps to numerical ID: {numerical_id}")
        return {"numerical_process_id": numerical_id}
    else:
        logging.warning(f"Selected process '{selected_process}' not found in mapping")
        return {"numerical_process_id": 1}

setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)

submit_job_task = KubernetesPodOperator(
    task_id="submit_job_task2",
    namespace=POD_NAMESPACE,
    image=DOCKER_IMAGE,
    name="ogc-submit-pod",
    env_vars=submit_job_env_vars,
    secrets=secret_env_vars,
    service_account_name="airflow-worker",
    in_cluster=True,
    get_logs=True,
    startup_timeout_seconds=600,
    container_security_context={"privileged": True},
    container_logs=True,
    do_xcom_push=True,
    dag=dag,
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

monitor_job_task = KubernetesPodOperator(
    task_id="monitor_job_task2",
    namespace=POD_NAMESPACE,
    image=DOCKER_IMAGE,
    name="ogc-monitor-pod",
    env_vars=monitor_job_env_vars,
    secrets=secret_env_vars,
    service_account_name="airflow-worker",
    in_cluster=True,
    get_logs=True,
    startup_timeout_seconds=600,
    container_security_context={"privileged": True},
    container_logs=True,
    dag=dag,
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

def cleanup(**context):
    """A placeholder cleanup task."""
    logging.info("Cleanup executed.")

cleanup_task = PythonOperator(
    task_id="Cleanup", python_callable=cleanup, dag=dag, trigger_rule=TriggerRule.ALL_DONE
)

chain(setup_task, submit_job_task, monitor_job_task, cleanup_task)