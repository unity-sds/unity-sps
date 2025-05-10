"""
DAG to execute VTLS processing in two stages (L1 and L2).
This DAG triggers cwl_dag_modular twice in sequence.
"""

import json
from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.python import get_current_context
from airflow.decorators import task
from datetime import datetime
from airflow.models.param import Param
from pprint import pprint
from airflow.utils.trigger_rule import TriggerRule


# Default DAG configuration
dag_default_args = {
    "owner": "VTLS_Owner",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}

with DAG(
    dag_id="execute_VTLS_DAG",
    schedule=None,
    tags=["L1_L2"],
    default_args=dag_default_args,
    catchup=False,
    params={
        # L1 Processing Parameters
        "stac_json": Param(
            default="https://raw.githubusercontent.com/unity-sds/unity-tutorial-application/refs/heads/main/test/stage_in/stage_in_results.json",
            type="string",
            title="STAC JSON",
            description="STAC JSON data to download granules encoded as a JSON string or the URL of a JSON or YAML file",
        ),
        "process_workflow": Param(
            default="https://raw.githubusercontent.com/example/l1-workflow.cwl",
            type="string",
            title="L1 Processing workflow",
            description="The processing workflow URL",
        ),
                # L2 specific parameters could be added here with different naming
        "l2_process_workflow": Param(
            default="https://raw.githubusercontent.com/example/l2-workflow.cwl",
            type="string",
            title="L2 Processing workflow",
            description="The L2 processing workflow URL",
        ),
        "process_args": Param(
            default=json.dumps({"level": "L1"}),
            type="string",
            title="Processing workflow parameters",
            description=("The processing job parameters encoded as a JSON string or the URL of a JSON or YAML file"),
        ),
        "log_level": Param(
            default="INFO",
            type="string",
            enum=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            title="Processing log levels",
            description=("Log level for processing"),
        ),
        "request_instance_type": Param(
            default="t3.medium",
            type="string",
            enum=["t3.medium", "t3.large", "t3.xlarge", "t3.2xlarge"],
            title="EC2 instance type",
        ),
        "request_storage": Param(
            default="10Gi", 
            type="string", 
            enum=["10Gi", "50Gi", "100Gi", "150Gi", "200Gi", "250Gi"],
            title="Storage request",
            description="Amount of storage to request for processing",
        ),
    },
) as dag:
    
    @task(task_id="prepare_l1_params")
    def prepare_l1_params(**context):
        """
        TaskFlow API approach: Using **context to access params.
        """
        # Extract parameters from the context
        context = get_current_context()
        pprint(context)
        params = context["params"]
        
        # Build configuration dictionary
        l1_config = {
            "stac_json": params["stac_json"],
            "process_workflow": params["process_workflow"],
            "process_args": params["process_args"],
            "log_level": params["log_level"],
            "request_instance_type": params["request_instance_type"],
            "request_storage": params["request_storage"],
        }
        
        print(f"L1 Configuration: {l1_config}")
        return l1_config
    
    @task(task_id="prepare_l2_params")
    def prepare_l2_params(**context):
        
        # Extract parameters from the context
        context = get_current_context()
        pprint(context)
        params = context["params"]

        print(f"xcom_pull value1: {context['ti'].xcom_pull(task_ids='cwl_task_processing', dag_id='cwl_dag_modular', include_prior_dates=True)}")
        l2_stac_json = context['ti'].xcom_pull(task_ids='cwl_task_processing', dag_id='cwl_dag_modular', include_prior_dates=True)

        l2_config = {
            "stac_json": l2_stac_json['stac_json'],
            "process_workflow": params["l2_process_workflow"],
            "process_args": params["process_args"],
            "log_level": params["log_level"],
            "request_instance_type": params["request_instance_type"],
            "request_storage": params["request_storage"],
        }
        
        print(f"L2 Configuration: {l2_config}")
        return l2_config

    # Get L1 parameters using TaskFlow API
    l1_params = prepare_l1_params()


    # Trigger the L1 processing
    # The parameter values come from the return value of prepare_l1_params task
    trigger_l1_cwl = TriggerDagRunOperator(
        task_id="trigger_L1_cwl",
        trigger_dag_id="cwl_dag_modular",
        trigger_rule=TriggerRule.ALL_SUCCESS,
        wait_for_completion=True,
        poke_interval=60,  # Check status every minute
        conf={
            "stac_json": "{{ ti.xcom_pull(task_ids='prepare_l1_params')['stac_json'] }}",
            "process_workflow": "{{ ti.xcom_pull(task_ids='prepare_l1_params')['process_workflow'] }}",
            "process_args": "{{ ti.xcom_pull(task_ids='prepare_l1_params')['process_args'] }}",
            "log_level": "{{ ti.xcom_pull(task_ids='prepare_l1_params')['log_level'] }}",
            "request_instance_type": "{{ ti.xcom_pull(task_ids='prepare_l1_params')['request_instance_type'] }}",
            "request_storage": "{{ ti.xcom_pull(task_ids='prepare_l1_params')['request_storage'] }}",
        },
    )
    
    # Get L2 parameters using TaskFlow API
    l2_params = prepare_l2_params()

    # Trigger the L2 processing
    # The parameter values come from the return value of prepare_l2_params operator
    trigger_l2_cwl = TriggerDagRunOperator(
        task_id="trigger_L2_cwl",
        trigger_dag_id="cwl_dag_modular",
        trigger_rule=TriggerRule.ALL_SUCCESS,
        wait_for_completion=True,
        poke_interval=60,  # Check status every minute
        conf={
            "stac_json": "{{ ti.xcom_pull(task_ids='prepare_l2_params')['stac_json'] }}",
            "process_workflow": "{{ ti.xcom_pull(task_ids='prepare_l2_params')['process_workflow'] }}",
            "process_args": "{{ ti.xcom_pull(task_ids='prepare_l2_params')['process_args'] }}",
            "log_level": "{{ ti.xcom_pull(task_ids='prepare_l2_params')['log_level'] }}",
            "request_instance_type": "{{ ti.xcom_pull(task_ids='prepare_l2_params')['request_instance_type'] }}",
            "request_storage": "{{ ti.xcom_pull(task_ids='prepare_l2_params')['request_storage'] }}",
        },
    )
    
    # Define dependencies
    # This shows how task outputs (which are automatically pushed to XCom)
    # are connected to downstream tasks
    l1_params >> trigger_l1_cwl >> l2_params >> trigger_l2_cwl
