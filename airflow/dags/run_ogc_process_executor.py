"""
OGC Process Executor DAG - Executes the actual OGC process with validated inputs.

This DAG is triggered by the launcher DAG (run_ogc_process2) and performs 
the actual process execution and monitoring.
"""
import json
import logging
from datetime import datetime
import requests
import re

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.models.baseoperator import BaseOperator, chain
from airflow.operators.python import PythonOperator, get_current_context
from airflow.utils.trigger_rule import TriggerRule
from airflow.exceptions import AirflowException
from airflow.providers.cncf.kubernetes.hooks.kubernetes import KubernetesHook
import time

K8S_SECRET_NAME = "sps-app-credentials"

def fetch_ogc_processes():
    """Fetch available processes from the OGC API and create mapping."""
    try:
        response = requests.get("https://api.dit.maap-project.org/api/ogc/processes", timeout=30)
        response.raise_for_status()
        
        processes_data = response.json()
        process_mapping = {}
        
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
                display_name = f"{process_id}:{process_version}" if process_version else process_id
                process_mapping[display_name] = numerical_id
        
        return process_mapping
        
    except requests.RequestException as e:
        logging.error(f"Failed to fetch processes: {e}")
        return {"example-process:1.0": 1}
    except Exception as e:
        logging.error(f"Error processing OGC processes: {e}")
        return {"example-process:1.0": 1}

PROCESS_MAPPING = fetch_ogc_processes()

class OGCSubmitJobOperator(BaseOperator):
    """Custom operator to submit jobs to OGC API endpoints."""
    
    template_fields = ("process_id", "job_inputs", "job_queue")
    
    def __init__(self, process_id, job_inputs, job_queue, 
                 submit_url_template="https://api.dit.maap-project.org/api/ogc/processes/{process_id}/execution",
                 **kwargs):
        super().__init__(**kwargs)
        self.process_id = process_id
        self.job_inputs = job_inputs
        self.job_queue = job_queue
        self.submit_url_template = submit_url_template
    
    def execute(self, context):
        """Submit job to OGC API and return job ID."""
        
        try:
            # Get MAAP token from Kubernetes secret
            k8s_hook = KubernetesHook()
            secret = k8s_hook.get_secret(name=K8S_SECRET_NAME, namespace=k8s_hook.get_namespace())
            maap_pgt = secret.data.get("MAAP_PGT")
            
            if maap_pgt:
                import base64
                maap_pgt = base64.b64decode(maap_pgt).decode('utf-8')
            else:
                raise AirflowException("MAAP_PGT token not found in Kubernetes secret")
            
            # Prepare URL and payload
            submit_url = self.submit_url_template.format(process_id=self.process_id)
            
            # Parse job inputs if it's a string
            if isinstance(self.job_inputs, str):
                try:
                    job_inputs_dict = json.loads(self.job_inputs)
                except json.JSONDecodeError:
                    job_inputs_dict = {}
            else:
                job_inputs_dict = self.job_inputs or {}
            
            payload = {
                "queue": self.job_queue,
                "inputs": job_inputs_dict
            }
            
            headers = {
                "proxy-ticket": maap_pgt,
                "Content-Type": "application/json"
            }
            
            self.log.info(f"Submitting job to {submit_url}")
            self.log.info(f"Job payload: {json.dumps(payload, indent=2)}")
            
            # Submit job
            response = requests.post(submit_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            job_id = result.get("id")
            
            if not job_id:
                raise AirflowException(f"Failed to get job ID from response: {result}")
            
            self.log.info(f"Job submitted successfully. Job ID: {job_id}")
            
            # Return job_id for next task
            return {"job_id": job_id}
            
        except requests.RequestException as e:
            self.log.error(f"HTTP request failed: {e}")
            raise AirflowException(f"Failed to submit job: {e}")
        except Exception as e:
            self.log.error(f"Job submission failed: {e}")
            raise AirflowException(f"Job submission error: {e}")


class OGCMonitorJobOperator(BaseOperator):
    """Custom operator to monitor OGC job status."""
    
    template_fields = ("job_id",)
    
    def __init__(self, job_id, 
                 monitor_url_template="https://api.dit.maap-project.org/api/ogc/jobs/{job_id}",
                 timeout=3600, poll_interval=30, **kwargs):
        super().__init__(**kwargs)
        self.job_id = job_id
        self.monitor_url_template = monitor_url_template
        self.timeout = timeout
        self.poll_interval = poll_interval
    
    def execute(self, context):
        """Monitor job status until completion or timeout."""
        
        try:
            self.log.info(f"Monitoring job with ID: {self.job_id}")

            # Get MAAP token from Kubernetes secret
            k8s_hook = KubernetesHook()
            secret = k8s_hook.get_secret(name=K8S_SECRET_NAME, namespace=k8s_hook.get_namespace())
            maap_pgt = secret.data.get("MAAP_PGT")
            
            if maap_pgt:
                import base64
                maap_pgt = base64.b64decode(maap_pgt).decode('utf-8')
            else:
                raise AirflowException("MAAP_PGT token not found in Kubernetes secret")
            
            monitor_url = self.monitor_url_template.format(job_id=self.job_id)
            headers = {
                "proxy-ticket": maap_pgt,
                "Content-Type": "application/json"
            }
            
            self.log.info(f"Monitoring job {self.job_id} at {monitor_url}")
            
            start_time = time.time()
            
            while time.time() - start_time < self.timeout:
                try:
                    response = requests.get(monitor_url, headers=headers, timeout=30)
                    response.raise_for_status()
                    
                    result = response.json()
                    status = result.get("status", "unknown")
                    
                    self.log.info(f"Job {self.job_id} status: {status}")
                    
                    if status == "successful":
                        self.log.info(f"Job {self.job_id} completed successfully!")
                        return {"status": "successful", "result": result}
                    elif status == "failed":
                        error_msg = result.get("message", "No error message provided")
                        self.log.error(f"Job {self.job_id} failed: {error_msg}")
                        raise AirflowException(f"Job {self.job_id} failed: {error_msg}")
                    elif status in ["running", "accepted", "processing"]:
                        self.log.info(f"Job {self.job_id} still {status}, waiting {self.poll_interval}s...")
                        time.sleep(self.poll_interval)
                    else:
                        self.log.warning(f"Unknown job status: {status}")
                        time.sleep(self.poll_interval)
                        
                except requests.RequestException as e:
                    self.log.warning(f"Request failed, retrying: {e}")
                    time.sleep(self.poll_interval)
                    continue
            
            # Timeout reached
            raise AirflowException(f"Job {self.job_id} monitoring timed out after {self.timeout} seconds")
            
        except Exception as e:
            self.log.error(f"Job monitoring failed: {e}")
            raise

dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}

# --- DAG Definition ---

dag = DAG(
    dag_id="run_ogc_process_executor",
    description="Executes OGC processes with validated inputs (triggered by launcher)",
    dag_display_name="OGC Process Executor",
    tags=["ogc", "executor", "triggered"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=10,
    default_args=dag_default_args,
    # This DAG expects to be triggered with conf parameters
)

# --- Task Definitions ---

def setup_execution(**context):
    """Setup task that processes the triggered DAG configuration."""
    
    logging.info("Setting up OGC process execution...")
    
    # Get configuration from trigger
    dag_run_conf = context.get('dag_run').conf or {}
    logging.info(f"Received configuration: {json.dumps(dag_run_conf, indent=2)}")
    
    selected_process = dag_run_conf.get('selected_process')
    queue = dag_run_conf.get('queue', 'maap-dps-sandbox')
    job_inputs = dag_run_conf.get('job_inputs', '{}')
    
    if not selected_process:
        raise AirflowException("No selected_process provided in trigger configuration")
    
    # Get numerical process ID
    numerical_id = PROCESS_MAPPING.get(selected_process)
    if not numerical_id:
        raise AirflowException(f"Process '{selected_process}' not found in mapping")
    
    logging.info(f"Selected process: {selected_process}")
    logging.info(f"Numerical process ID: {numerical_id}")
    logging.info(f"Queue: {queue}")
    logging.info(f"Job inputs: {job_inputs}")
    
    return {
        "selected_process": selected_process,
        "numerical_process_id": numerical_id,
        "queue": queue,
        "job_inputs": job_inputs
    }

setup_task = PythonOperator(
    task_id="setup_execution",
    python_callable=setup_execution,
    dag=dag,
)

submit_job_task = OGCSubmitJobOperator(
    task_id="submit_job",
    process_id="{{ ti.xcom_pull(task_ids='setup_execution', key='return_value')['numerical_process_id'] }}",
    job_inputs="{{ ti.xcom_pull(task_ids='setup_execution', key='return_value')['job_inputs'] }}",
    job_queue="{{ ti.xcom_pull(task_ids='setup_execution', key='return_value')['queue'] }}",
    dag=dag,
)

monitor_job_task = OGCMonitorJobOperator(
    task_id="monitor_job",
    job_id="{{ ti.xcom_pull(task_ids='submit_job', key='return_value')['job_id'] }}",
    timeout=3600,
    poll_interval=30,
    dag=dag,
)

def cleanup_execution(**context):
    """Cleanup and final reporting."""
    
    logging.info("OGC process execution completed.")
    
    # Get results from previous tasks
    setup_result = context['ti'].xcom_pull(task_ids='setup_execution', key='return_value')
    submit_result = context['ti'].xcom_pull(task_ids='submit_job', key='return_value')
    monitor_result = context['ti'].xcom_pull(task_ids='monitor_job', key='return_value')
    
    logging.info("=" * 60)
    logging.info("EXECUTION SUMMARY")
    logging.info("=" * 60)
    
    if setup_result:
        logging.info(f"Process: {setup_result.get('selected_process')}")
        logging.info(f"Process ID: {setup_result.get('numerical_process_id')}")
        logging.info(f"Queue: {setup_result.get('queue')}")
    
    if submit_result:
        logging.info(f"Job ID: {submit_result.get('job_id')}")
    
    if monitor_result:
        logging.info(f"Final Status: {monitor_result.get('status')}")
        
    logging.info("=" * 60)

cleanup_task = PythonOperator(
    task_id="cleanup_execution",
    python_callable=cleanup_execution,
    dag=dag,
    trigger_rule=TriggerRule.ALL_DONE
)

chain(setup_task, submit_job_task, monitor_job_task, cleanup_task)