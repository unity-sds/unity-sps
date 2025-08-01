"""
OGC Process Selector DAG - Step 1: User selects a process and this creates/updates 
dynamic input DAGs with specific fields for that process.
"""
import json
import logging
from datetime import datetime
import requests
import re
import os

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowException
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
        return {"example-process:1.0": 1}, ["example-process:1.0"]
    except Exception as e:
        logging.error(f"Error processing OGC processes: {e}")
        return {"example-process:1.0": 1}, ["example-process:1.0"]

# Constants
PROCESS_MAPPING, DROPDOWN_OPTIONS = fetch_ogc_processes()

dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}

# --- DAG Definition ---

dag = DAG(
    dag_id="ogc_process_selector",
    description="Step 1: Select an OGC process to create dynamic input DAG",
    dag_display_name="🔧 Step 1: Select OGC Process",
    tags=["ogc", "step1", "selector"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=10,
    default_args=dag_default_args,
    params={
        "selected_process": Param(
            default=DROPDOWN_OPTIONS[0] if DROPDOWN_OPTIONS else "example-process:1.0",
            enum=DROPDOWN_OPTIONS,
            title="🎯 Select Process",
            description=f"Choose a process to configure. Available: {', '.join(DROPDOWN_OPTIONS[:3])}{'...' if len(DROPDOWN_OPTIONS) > 3 else ''}",
        ),
        "queue": Param(
            "maap-dps-sandbox",
            type="string",
            title="🚀 Execution Queue",
            description="The MAAP queue to submit the job to",
        ),
    },
)

def create_dynamic_input_dag(**context):
    """Create a dynamic input DAG for the selected process."""
    
    selected_process = context['params'].get('selected_process')
    queue = context['params'].get('queue', 'maap-dps-sandbox')
    
    if not selected_process or selected_process not in PROCESS_MAPPING:
        raise AirflowException(f"Invalid process selection: {selected_process}")
    
    numerical_id = PROCESS_MAPPING[selected_process]
    logging.info(f"Creating input DAG for process '{selected_process}' (ID: {numerical_id})")
    
    # Fetch process schema
    try:
        process_url = f"https://api.dit.maap-project.org/api/ogc/processes/{numerical_id}"
        response = requests.get(process_url, timeout=30)
        response.raise_for_status()
        
        process_details = response.json()
        inputs_schema = process_details.get("inputs", {})
        process_title = process_details.get("title", selected_process)
        process_description = process_details.get("description", "No description available")
        
        logging.info(f"Process: {process_title}")
        logging.info(f"Description: {process_description}")
        logging.info(f"Input fields: {list(inputs_schema.keys())}")
        
    except requests.RequestException as e:
        raise AirflowException(f"Failed to fetch process schema: {e}")
    
    # Generate the dynamic DAG file
    dag_content = generate_input_dag_content(
        selected_process=selected_process,
        numerical_id=numerical_id,
        inputs_schema=inputs_schema,
        process_title=process_title,
        process_description=process_description,
        queue=queue
    )
    
    # Write the DAG file
    dags_folder = os.path.dirname(os.path.abspath(__file__))
    safe_process_name = selected_process.replace(":", "_").replace("-", "_")
    dag_filename = f"ogc_input_{safe_process_name}.py"
    dag_filepath = os.path.join(dags_folder, dag_filename)
    
    try:
        with open(dag_filepath, 'w') as f:
            f.write(dag_content)
        
        logging.info(f"✅ Created dynamic input DAG: {dag_filename}")
        logging.info("=" * 60)
        logging.info("🎉 SUCCESS! Your input DAG has been created!")
        logging.info("=" * 60)
        logging.info(f"📋 Process: {process_title}")
        logging.info(f"🆔 DAG ID: ogc_input_{safe_process_name}")
        logging.info(f"📁 File: {dag_filename}")
        logging.info("=" * 60)
        logging.info("📝 NEXT STEPS:")
        logging.info("1. Wait 10-30 seconds for Airflow to detect the new DAG")
        logging.info(f"2. Look for DAG: 'Step 2: {process_title} - Inputs'")
        logging.info("3. Run that DAG to configure your process inputs")
        logging.info("=" * 60)
        
        return {
            "success": True,
            "dag_id": f"ogc_input_{safe_process_name}",
            "dag_file": dag_filename,
            "process_title": process_title,
            "input_count": len(inputs_schema)
        }
        
    except Exception as e:
        logging.error(f"Failed to write DAG file: {e}")
        raise AirflowException(f"Failed to create input DAG: {e}")

def generate_input_dag_content(selected_process, numerical_id, inputs_schema, process_title, process_description, queue):
    """Generate the content for the dynamic input DAG."""
    
    safe_process_name = selected_process.replace(":", "_").replace("-", "_")
    
    # Generate Param definitions for each input
    param_definitions = []
    for input_key, input_def in inputs_schema.items():
        input_title = input_def.get('title', input_key)
        input_desc = input_def.get('description', f'Input for {input_key}')
        input_type = input_def.get('type', 'string')
        input_default = input_def.get('default')
        input_placeholder = input_def.get('placeholder', '')
        
        # Map OGC types to Airflow Param types
        if input_type in ['text', 'string']:
            param_type = 'string'
            default_value = input_default or input_placeholder or ""
        elif input_type in ['number', 'integer', 'float']:
            param_type = 'number'
            default_value = input_default or 0
        elif input_type == 'boolean':
            param_type = 'boolean' 
            default_value = input_default or False
        else:
            param_type = 'string'
            default_value = input_default or ""
        
        # Create description with type info
        full_description = f"{input_desc}"
        if input_placeholder:
            full_description += f" (e.g., {input_placeholder})"
        
        param_def = f'''        "{input_key}": Param(
            default={repr(default_value)},
            type="{param_type}",
            title="🔧 {input_title}",
            description="{full_description}",
        ),'''
        
        param_definitions.append(param_def)
    
    params_section = "\n".join(param_definitions)
    
    # Generate the DAG content
    dag_content = f'''"""
Dynamic Input DAG for {process_title}
Generated automatically for process: {selected_process}

{process_description}
"""
import json
import logging
from datetime import datetime

from airflow.models.dag import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.exceptions import AirflowException

dag_default_args = {{
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}}

# Process configuration
SELECTED_PROCESS = "{selected_process}"
NUMERICAL_ID = {numerical_id}
PROCESS_TITLE = "{process_title}"
DEFAULT_QUEUE = "{queue}"

# Input schema
INPUTS_SCHEMA = {json.dumps(inputs_schema, indent=4)}

# --- DAG Definition ---

dag = DAG(
    dag_id="ogc_input_{safe_process_name}",
    description="Step 2: Configure inputs for {process_title}",
    dag_display_name="⚙️ Step 2: {process_title} - Inputs",
    tags=["ogc", "step2", "inputs", "{safe_process_name}"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=5,
    default_args=dag_default_args,
    params={{
{params_section}
        "queue": Param(
            default=DEFAULT_QUEUE,
            type="string",
            title="🚀 Execution Queue",
            description="The MAAP queue to submit the job to",
        ),
    }},
)

def validate_and_trigger_execution(**context):
    """Validate inputs and trigger the execution DAG."""
    
    logging.info("Validating inputs and preparing execution...")
    logging.info(f"Process: {{PROCESS_TITLE}}")
    logging.info(f"Process ID: {{NUMERICAL_ID}}")
    
    # Collect all input values
    validated_inputs = {{}}
    params = context['params']
    
    for input_key, input_def in INPUTS_SCHEMA.items():
        if input_key in params:
            value = params[input_key]
            validated_inputs[input_key] = value
            logging.info(f"✓ {{input_key}}: {{value}}")
        elif input_def.get('default') is not None:
            default_value = input_def.get('default')
            validated_inputs[input_key] = default_value
            logging.info(f"→ {{input_key}}: {{default_value}} (default)")
        else:
            logging.warning(f"⚠ No value for {{input_key}}")
    
    queue = params.get('queue', DEFAULT_QUEUE)
    
    # Prepare execution parameters
    execution_params = {{
        "selected_process": SELECTED_PROCESS,
        "numerical_process_id": NUMERICAL_ID,
        "queue": queue,
        "job_inputs": json.dumps(validated_inputs),
        "process_title": PROCESS_TITLE
    }}
    
    logging.info("=" * 60)
    logging.info("🚀 TRIGGERING EXECUTION")
    logging.info("=" * 60)
    logging.info(f"Final inputs: {{json.dumps(validated_inputs, indent=2)}}")
    logging.info(f"Queue: {{queue}}")
    logging.info("=" * 60)
    
    return {{
        "execution_params": execution_params,
        "validated_inputs": validated_inputs
    }}

def execution_summary(**context):
    """Provide execution summary."""
    
    validation_result = context['ti'].xcom_pull(task_ids='validate_inputs')
    
    logging.info("=" * 60) 
    logging.info("✅ INPUT VALIDATION COMPLETED")
    logging.info("=" * 60)
    logging.info(f"Process: {{PROCESS_TITLE}}")
    logging.info(f"Input fields configured: {{len(validation_result['validated_inputs'])}}")
    logging.info("The execution DAG has been triggered!")
    logging.info("Check the 'ogc_process_executor' DAG for progress.")
    logging.info("=" * 60)

# Task to validate inputs
validate_task = PythonOperator(
    task_id="validate_inputs",
    python_callable=validate_and_trigger_execution,
    dag=dag,
)

# Task to trigger execution
trigger_task = TriggerDagRunOperator(
    task_id="trigger_execution",
    trigger_dag_id="ogc_process_executor",
    conf="{{{{ ti.xcom_pull(task_ids='validate_inputs')['execution_params'] }}}}",
    wait_for_completion=False,
    dag=dag,
)

# Summary task
summary_task = PythonOperator(
    task_id="execution_summary", 
    python_callable=execution_summary,
    dag=dag,
)

validate_task >> trigger_task >> summary_task
'''
    
    return dag_content

# Task to create the dynamic DAG
create_dag_task = PythonOperator(
    task_id="create_input_dag",
    python_callable=create_dynamic_input_dag,
    dag=dag,
)

def completion_message(**context):
    """Display completion message with next steps."""
    
    result = context['ti'].xcom_pull(task_ids='create_input_dag')
    
    if result and result.get('success'):
        logging.info("=" * 60)
        logging.info("🎉 PROCESS SELECTION COMPLETED!")
        logging.info("=" * 60)
        logging.info(f"📋 Process: {result['process_title']}")
        logging.info(f"🆔 Input DAG ID: {result['dag_id']}")
        logging.info(f"📊 Input fields: {result['input_count']}")
        logging.info("=" * 60)
        logging.info("📝 WHAT'S NEXT:")
        logging.info("1. Wait 10-30 seconds for the new DAG to appear")
        logging.info(f"2. Look for: 'Step 2: {result['process_title']} - Inputs'")
        logging.info("3. Run that DAG to configure your specific inputs")
        logging.info("4. The execution will be triggered automatically")
        logging.info("=" * 60)
    else:
        logging.error("Failed to create input DAG")

completion_task = PythonOperator(
    task_id="completion_message",
    python_callable=completion_message,
    dag=dag,
)

create_dag_task >> completion_task