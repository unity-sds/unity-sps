"""
Dynamic OGC Process Launcher DAG - Fetches process input schema and triggers execution DAG.

This DAG works in two stages:
1. User selects a process and this DAG fetches the input schema
2. This DAG triggers the execution DAG with the proper input parameters
"""
import json
import logging
from datetime import datetime
import requests
import re

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.models.baseoperator import chain
from airflow.operators.python import PythonOperator, get_current_context
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.exceptions import AirflowException
from airflow.providers.cncf.kubernetes.hooks.kubernetes import KubernetesHook
import time

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
                display_name = f"{process_id}:{process_version}" if process_version else process_id
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

def get_maap_token():
    """Helper function to get MAAP token from Kubernetes secret."""
    try:
        k8s_hook = KubernetesHook()
        secret = k8s_hook.get_secret(name="sps-app-credentials", namespace=k8s_hook.get_namespace())
        maap_pgt = secret.data.get("MAAP_PGT")
        
        if maap_pgt:
            import base64
            return base64.b64decode(maap_pgt).decode('utf-8')
        else:
            raise AirflowException("MAAP_PGT token not found in Kubernetes secret")
    except Exception as e:
        logging.error(f"Failed to get MAAP token: {e}")
        return None

# Constants
K8S_SECRET_NAME = "sps-app-credentials"
PROCESS_MAPPING, DROPDOWN_OPTIONS = fetch_ogc_processes()

dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}

# --- DAG Definition ---

dag = DAG(
    dag_id="run_ogc_process2",
    description="Dynamic OGC Process Launcher - Fetches input schema and triggers execution",
    dag_display_name="OGC Process Launcher (Dynamic Inputs)",
    tags=["ogc", "launcher", "dynamic"],
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
        # Dynamic input fields will be populated based on process schema
        "dynamic_inputs": Param(
            "{}",
            type="string",
            title="Process Inputs (JSON)",
            description="Enter process inputs as JSON. Schema will be displayed in logs after process selection.",
        )
    },
)

# --- Task Definitions ---

def fetch_process_schema(**context):
    """Fetch the input schema for the selected process."""
    
    logging.info("Fetching process input schema...")
    
    selected_process = context['params'].get('selected_process')
    if not selected_process or selected_process not in PROCESS_MAPPING:
        raise AirflowException(f"Invalid process selection: {selected_process}")
    
    numerical_id = PROCESS_MAPPING[selected_process]
    logging.info(f"Selected process '{selected_process}' maps to numerical ID: {numerical_id}")
    
    # Fetch process details
    try:
        
        process_url = f"https://api.dit.maap-project.org/api/ogc/processes/{numerical_id}"
        response = requests.get(process_url, timeout=30)
        response.raise_for_status()
        
        process_details = response.json()
        inputs_schema = process_details.get("inputs", {})
        
        logging.info(f"Process Details URL: {process_url}")
        logging.info(f"Process Title: {process_details.get('title', 'N/A')}")
        logging.info(f"Process Description: {process_details.get('description', 'N/A')}")
        logging.info("=" * 60)
        logging.info("INPUT SCHEMA FOR THIS PROCESS:")
        logging.info("=" * 60)
        
        # Format the schema nicely for logging
        for input_key, input_def in inputs_schema.items():
            logging.info(f"Input: {input_key}")
            logging.info(f"  Title: {input_def.get('title', input_key)}")
            logging.info(f"  Description: {input_def.get('description', 'No description')}")
            logging.info(f"  Type: {input_def.get('type', 'unknown')}")
            logging.info(f"  Default: {input_def.get('default', 'None')}")
            if input_def.get('placeholder'):
                logging.info(f"  Placeholder: {input_def.get('placeholder')}")
            logging.info("-" * 40)
        
        logging.info("=" * 60)
        logging.info("EXAMPLE JSON INPUT:")
        logging.info("=" * 60)
        
        # Create example JSON input
        example_inputs = {}
        for input_key, input_def in inputs_schema.items():
            if input_def.get('default') is not None:
                example_inputs[input_key] = input_def.get('default')
            elif input_def.get('placeholder'):
                example_inputs[input_key] = input_def.get('placeholder')
            else:
                input_type = input_def.get('type', 'string')
                if input_type == 'text' or input_type == 'string':
                    example_inputs[input_key] = f"example_{input_key}_value"
                elif input_type == 'number' or input_type == 'integer':
                    example_inputs[input_key] = 0
                elif input_type == 'boolean':
                    example_inputs[input_key] = True
                else:
                    example_inputs[input_key] = f"example_{input_key}_value"
        
        example_json = json.dumps(example_inputs, indent=2)
        logging.info(example_json)
        
        logging.info("=" * 60)
        logging.info("INSTRUCTIONS:")
        logging.info("Copy the example JSON above, modify the values as needed,")
        logging.info("and paste it into the 'Process Inputs (JSON)' field when")
        logging.info("re-triggering this DAG.")
        logging.info("=" * 60)
        
        return {
            "numerical_process_id": numerical_id,
            "selected_process": selected_process,
            "inputs_schema": inputs_schema,
            "example_inputs": example_inputs,
            "schema_fetched": True
        }
        
    except requests.RequestException as e:
        logging.error(f"Failed to fetch process schema: {e}")
        raise AirflowException(f"Failed to fetch process schema: {e}")

def validate_and_trigger_execution(**context):
    """Validate the dynamic inputs and trigger the execution DAG."""
    
    logging.info("Validating inputs and preparing execution...")
    
    # Get schema info from previous task
    schema_info = context['ti'].xcom_pull(task_ids='fetch_schema')
    if not schema_info or not schema_info.get('schema_fetched'):
        raise AirflowException("Schema was not properly fetched")
    
    selected_process = schema_info['selected_process']
    numerical_process_id = schema_info['numerical_process_id']
    inputs_schema = schema_info['inputs_schema']
    
    # Parse user-provided dynamic inputs
    dynamic_inputs_str = context['params'].get('dynamic_inputs', '{}')
    try:
        dynamic_inputs = json.loads(dynamic_inputs_str) if dynamic_inputs_str != '{}' else {}
    except json.JSONDecodeError as e:
        raise AirflowException(f"Invalid JSON in dynamic_inputs: {e}")
    
    logging.info(f"User provided inputs: {dynamic_inputs}")
    
    # Validate inputs against schema
    validated_inputs = {}
    for input_key, input_def in inputs_schema.items():
        if input_key in dynamic_inputs:
            validated_inputs[input_key] = dynamic_inputs[input_key]
            logging.info(f"✓ Using provided value for '{input_key}': {dynamic_inputs[input_key]}")
        elif input_def.get('default') is not None:
            validated_inputs[input_key] = input_def.get('default')
            logging.info(f"→ Using default value for '{input_key}': {input_def.get('default')}")
        else:
            logging.warning(f"⚠ No value provided for required input '{input_key}'")
    
    # If no inputs were provided, show schema again and stop
    if not dynamic_inputs:
        logging.info("=" * 60)
        logging.info("NO INPUTS PROVIDED - DISPLAYING SCHEMA AGAIN")
        logging.info("=" * 60)
        logging.info("Please provide inputs in the 'Process Inputs (JSON)' field")
        logging.info("and re-trigger this DAG to proceed with execution.")
        logging.info("=" * 60)
        return {
            "action": "schema_display_only",
            "message": "Re-trigger DAG with proper inputs to execute the process"
        }
    
    logging.info(f"Final validated inputs: {json.dumps(validated_inputs, indent=2)}")
    
    # Prepare parameters for execution DAG
    execution_params = {
        "selected_process": selected_process,
        "queue": context['params'].get('queue', 'maap-dps-sandbox'),
        "job_inputs": json.dumps(validated_inputs)
    }
    
    logging.info("=" * 60)
    logging.info("TRIGGERING EXECUTION DAG")
    logging.info("=" * 60)
    logging.info(f"Execution parameters: {json.dumps(execution_params, indent=2)}")
    
    return {
        "action": "trigger_execution",
        "execution_params": execution_params,
        "numerical_process_id": numerical_process_id
    }

# Task to fetch process schema
fetch_schema_task = PythonOperator(
    task_id="fetch_schema",
    python_callable=fetch_process_schema,
    dag=dag,
)

# Task to validate inputs and prepare execution
validate_inputs_task = PythonOperator(
    task_id="validate_inputs",
    python_callable=validate_and_trigger_execution,
    dag=dag,
)

# Task to trigger the execution DAG
trigger_execution_task = TriggerDagRunOperator(
    task_id="trigger_execution",
    trigger_dag_id="run_ogc_process_executor",  # This DAG needs to be created
    conf="{{ ti.xcom_pull(task_ids='validate_inputs', key='return_value')['execution_params'] }}",
    wait_for_completion=False,
    dag=dag,
    trigger_rule="none_failed",  # Only run if validation succeeded
)

def completion_summary(**context):
    """Provide a summary of what happened."""
    
    validation_result = context['ti'].xcom_pull(task_ids='validate_inputs', key='return_value')
    
    if validation_result and validation_result.get('action') == 'schema_display_only':
        logging.info("=" * 60)
        logging.info("LAUNCHER DAG COMPLETED - SCHEMA DISPLAY MODE")
        logging.info("=" * 60)
        logging.info("The process schema has been displayed in the logs.")
        logging.info("Please check the 'fetch_schema' task logs for the input schema")
        logging.info("and re-trigger this DAG with proper inputs to execute.")
        logging.info("=" * 60)
    elif validation_result and validation_result.get('action') == 'trigger_execution':
        logging.info("=" * 60)
        logging.info("LAUNCHER DAG COMPLETED - EXECUTION TRIGGERED")
        logging.info("=" * 60)
        logging.info("The execution DAG has been triggered successfully.")
        logging.info("Check the 'run_ogc_process_executor' DAG for execution progress.")
        logging.info("=" * 60)
    else:
        logging.info("DAG completed with unknown status")

summary_task = PythonOperator(
    task_id="completion_summary",
    python_callable=completion_summary,
    dag=dag,
    trigger_rule="none_failed_min_one_success",
)

# Chain the tasks
chain(
    fetch_schema_task,
    validate_inputs_task,
    [trigger_execution_task, summary_task]
)