"""
DAG with two separate tasks to submit a job to an OGC-compliant process API
and then monitor its status.
"""
import json
import logging
from datetime import datetime
import os
import requests

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.models.baseoperator import BaseOperator, chain
from airflow.operators.python import PythonOperator, get_current_context
from airflow.utils.trigger_rule import TriggerRule
from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook
import time

K8S_SECRET_NAME = "sps-app-credentials"

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
            # Get MAAP token from Airflow connection
            connection = BaseHook.get_connection('maap_api_pgt')
            maap_pgt = connection.password
                
            if not maap_pgt:
                raise AirflowException("MAAP_PGT token not found in Airflow connection")
            
            # Extract process ID if in format "id:version"
            #actual_process_id = self.process_id.split(':')[0] if ':' in str(self.process_id) else self.process_id
            
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

            # Get MAAP token from Airflow connection
            connection = BaseHook.get_connection('maap_api_pgt')
            maap_pgt = connection.password
                
            if not maap_pgt:
                raise AirflowException("MAAP_PGT token not found in Airflow connection")
            
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
        "job_queue": Param(
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

def setup(ti=None,**context):
    """Task that selects the proper Karpenter Node Pool depending on the user requested resources."""

    logging.info("Starting OGC job submission and monitoring DAG.")
    logging.info(f"Parameters received: {context['params']}")
    context = get_current_context()
    logging.info(f"DAG Run parameters: {json.dumps(context['params'], sort_keys=True, indent=4)}")

setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)

submit_job_task = OGCSubmitJobOperator(
    task_id="submit_job_task",
    process_id="{{ params.process_id }}",
    job_inputs="{{ params.job_inputs }}",
    job_queue="{{ params.job_queue }}",
    dag=dag,
)

monitor_job_task = OGCMonitorJobOperator(
    task_id="monitor_job_task",
    job_id="{{ ti.xcom_pull(task_ids='submit_job_task', key='return_value')['job_id'] }}",
    timeout=3600,
    poll_interval=30,
    dag=dag,
)

def cleanup(**context):
    """A placeholder cleanup task."""
    logging.info("Cleanup executed.")

cleanup_task = PythonOperator(
    task_id="Cleanup", python_callable=cleanup, dag=dag, trigger_rule=TriggerRule.ALL_DONE
)

chain(setup_task, submit_job_task, monitor_job_task, cleanup_task)