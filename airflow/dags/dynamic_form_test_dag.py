"""
Dynamic Form Test DAG

This DAG demonstrates dynamic form functionality where:
- Initial dropdown has options a, b, c
- Option a shows fields 1 and 2
- Option b shows fields 3 and 4  
- Option c shows fields 5 and 6

To use this DAG:
1. Access the form at: http://localhost:8080/dynamic_form/dynamic_form_test
2. Select an option from the dropdown
3. Fill in the conditional fields that appear
4. Submit to trigger the DAG with the form data
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import logging

logger = logging.getLogger(__name__)

default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def process_form_data(**context):
    """Process the form data received from the dynamic form"""
    conf = context.get('dag_run').conf or {}
    
    logger.info("=== Dynamic Form Data Processing ===")
    logger.info(f"Received configuration: {conf}")
    
    main_option = conf.get('main_option')
    logger.info(f"Main option selected: {main_option}")
    
    if main_option == 'a':
        field_1 = conf.get('field_1', '')
        field_2 = conf.get('field_2', '')
        logger.info(f"Option A selected - Field 1: {field_1}, Field 2: {field_2}")
        print(f"Processing Option A with values: Field 1='{field_1}', Field 2='{field_2}'")
        
    elif main_option == 'b':
        field_3 = conf.get('field_3', '')
        field_4 = conf.get('field_4', '')
        logger.info(f"Option B selected - Field 3: {field_3}, Field 4: {field_4}")
        print(f"Processing Option B with values: Field 3='{field_3}', Field 4='{field_4}'")
        
    elif main_option == 'c':
        field_5 = conf.get('field_5', '')
        field_6 = conf.get('field_6', '')
        logger.info(f"Option C selected - Field 5: {field_5}, Field 6: {field_6}")
        print(f"Processing Option C with values: Field 5='{field_5}', Field 6='{field_6}'")
        
    else:
        logger.warning(f"Unknown or missing main_option: {main_option}")
        print(f"Warning: Unknown option '{main_option}' or no option provided")
    
    return f"Successfully processed form data for option: {main_option}"

def validate_form_data(**context):
    """Validate the form data received"""
    conf = context.get('dag_run').conf or {}
    
    main_option = conf.get('main_option')
    
    if not main_option:
        raise ValueError("No main_option provided in form data")
    
    if main_option not in ['a', 'b', 'c']:
        raise ValueError(f"Invalid main_option: {main_option}. Must be 'a', 'b', or 'c'")
    
    # Validate required fields based on option
    if main_option == 'a':
        if not conf.get('field_1') or not conf.get('field_2'):
            raise ValueError("Option A requires both field_1 and field_2 to be filled")
    elif main_option == 'b':
        if not conf.get('field_3') or not conf.get('field_4'):
            raise ValueError("Option B requires both field_3 and field_4 to be filled")
    elif main_option == 'c':
        if not conf.get('field_5') or not conf.get('field_6'):
            raise ValueError("Option C requires both field_5 and field_6 to be filled")
    
    logger.info("Form data validation passed")
    return "Validation successful"

def simulate_processing(**context):
    """Simulate some processing based on the selected option"""
    conf = context.get('dag_run').conf or {}
    main_option = conf.get('main_option')
    
    import time
    
    if main_option == 'a':
        logger.info("Simulating processing for Option A...")
        print("Executing Option A workflow...")
        time.sleep(5)  # Simulate work
        print("Option A processing completed")
        
    elif main_option == 'b':
        logger.info("Simulating processing for Option B...")
        print("Executing Option B workflow...")
        time.sleep(3)  # Simulate work
        print("Option B processing completed")
        
    elif main_option == 'c':
        logger.info("Simulating processing for Option C...")
        print("Executing Option C workflow...")
        time.sleep(7)  # Simulate work
        print("Option C processing completed")
    
    return f"Processing completed for option {main_option}"

# Create the DAG
with DAG(
    dag_id="dynamic_form_test",
    default_args=default_args,
    description="Test DAG for dynamic form functionality",
    schedule=None,  # Only triggered manually via form
    is_paused_upon_creation=False,
    catchup=False,
    tags=["test", "dynamic-form", "proof-of-concept"],
    doc_md=__doc__,
) as dag:
    
    # Task 1: Validate form data
    validate_task = PythonOperator(
        task_id="validate_form_data",
        python_callable=validate_form_data,
        doc_md="Validates that required form fields are present based on selected option"
    )
    
    # Task 2: Process form data
    process_task = PythonOperator(
        task_id="process_form_data", 
        python_callable=process_form_data,
        doc_md="Processes and logs the form data received from the dynamic form"
    )
    
    # Task 3: Simulate processing
    simulate_task = PythonOperator(
        task_id="simulate_processing",
        python_callable=simulate_processing,
        doc_md="Simulates different processing workflows based on the selected option"
    )
    
    # Set task dependencies
    validate_task >> process_task >> simulate_task