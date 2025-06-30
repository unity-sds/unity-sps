"""
DAG to execute the Docker container to run the App Generator package
"""

import json
import logging
import os
from datetime import datetime

import boto3
from airflow.models.baseoperator import chain
from airflow.models.param import Param
from airflow.operators.python import PythonOperator, get_current_context
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.utils.trigger_rule import TriggerRule
from kubernetes.client import models as k8s
from airflow.kubernetes.secret import Secret
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
from airflow.providers.cncf.kubernetes.secret import Secret as AirflowK8sSecret

from airflow import DAG

CONTAINER_RESOURCES = k8s.V1ResourceRequirements(
    requests={
        "ephemeral-storage": "{{ params.request_storage }} ",
    }
)

K8S_SECRET_NAME = "sps-app-credentials" # Must match metadata.name in kubernetes_secret

# <<<
LOG_LEVEL_TYPE = {10: "DEBUG", 20: "INFO"}

# Change this to the Docker image that contains the Application Package Generator
DOCKER_IMAGE = "jplmdps/unity-app-gen:v1.1.1"

# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}

dag = DAG(
    dag_id="appgen_dag",
    description="Application Package Generator DAG",
    dag_display_name="Application Package Generator DAG",
    tags=["AppGen"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=10,
    max_active_tasks=30,
    default_args=dag_default_args,
    params={
        "repository": Param(
            "https://github.com/unity-sds/unity-example-application",
            type="string",
            title="Repository",
            description="Git URL of application source files",
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

app_gen_env_vars = [
    k8s.V1EnvVar(
        name="DOCKSTORE_API_URL",
        value="http://awslbdockstorestack-lb-1429770210.us-west-2.elb.amazonaws.com:9998/api",
    ),
    k8s.V1EnvVar(name="GITHUB_REPO", value="{{ params.repository }}"),
]

secret_env_vars = [
    AirflowK8sSecret(
        deploy_type='env',                              # Expose as environment variable
        deploy_target='DOCKERHUB_USERNAME',             # Name of the ENV VAR inside our docker container 
        secret=K8S_SECRET_NAME,                         # Name of the K8s Secret
        key='DOCKERHUB_USERNAME'                        # Key in the K8s Secret's data field defined in main.tf
    ),
    AirflowK8sSecret(
        deploy_type='env',
        deploy_target='DOCKERHUB_TOKEN',
        secret=K8S_SECRET_NAME,
        key='DOCKERHUB_TOKEN'
    ),
    AirflowK8sSecret(
        deploy_type='env',
        deploy_target='DOCKSTORE_TOKEN',
        secret=K8S_SECRET_NAME,
        key='DOCKSTORE_TOKEN'
    )
]

def setup(ti=None, **context):
    """
    Task that selects the proper Karpenter Node Pool depending on the user requested resources.
    """

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

appgen_task = KubernetesPodOperator(
    retries=1,
    task_id="appgen_task",
    namespace=POD_NAMESPACE,
    env_vars=app_gen_env_vars,
    secrets=secret_env_vars,
    name="appgen-task-pod",
    image=DOCKER_IMAGE,
    service_account_name="airflow-worker",
    in_cluster=True,
    get_logs=True,
    startup_timeout_seconds=600,
    arguments=[
        "-r",
        "{{ params.repository }}",
        "-l",
        "{{ params.log_level }}",
        "-e",
        "{{ ti.xcom_pull(task_ids='Setup', key='ecr_login') }}",
    ],
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


def cleanup(**context):
    """
    This task is just a placeholder for now
    """
    logging.info("Cleanup executed")


cleanup_task = PythonOperator(
    task_id="Cleanup", python_callable=cleanup, dag=dag, trigger_rule=TriggerRule.ALL_DONE
)


chain(setup_task.as_setup(), appgen_task, cleanup_task.as_teardown(setups=setup_task))