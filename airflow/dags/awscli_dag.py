import uuid
from datetime import datetime

from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from kubernetes.client import models as k8s

from airflow import DAG

POD_TEMPLATE_FILE = "/opt/airflow/dags/aws_cli_pod.yaml"

# The Kubernetes namespace within which the Pod is run (it must already exist)
POD_NAMESPACE = "airflow"

# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}

# The DAG
dag = DAG(
    dag_id="awscli-dag",
    description="DAG to execute AWS CLI",
    is_paused_upon_creation=False,
    catchup=False,
    schedule_interval=None,
    max_active_runs=1,
    default_args=dag_default_args,
    # params={
    #    "cwl_workflow": Param(default_cwl_workflow, type="string"),
    #    "args_as_json": Param(default_args_as_json, type="string"),
    # }
)

# Environment variables
default_env_vars = {}

# This section defines KubernetesPodOperator
cwl_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    name="awscli-task",
    is_delete_operator_pod=True,
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="awscli-task",
    full_pod_spec=k8s.V1Pod(
        metadata=k8s.V1ObjectMeta(name="awscli-pod-" + uuid.uuid4().hex),
    ),
    pod_template_file=POD_TEMPLATE_FILE,
    # arguments=["{{ params.cwl_workflow }}", "{{ params.args_as_json }}"],
    dag=dag,
)
