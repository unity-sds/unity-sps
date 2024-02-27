import uuid
from datetime import datetime

from airflow.models.param import Param
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from kubernetes.client import models as k8s

from airflow import DAG

# The Kubernetes Pod that executes the CWL-Docker container
# Must use elevated privileges to start/stop the Docker engine
POD_TEMPLATE_FILE = "/opt/airflow/dags/docker_cwl_pod.yaml"

# The Kubernetes namespace within which the Pod is run (it must already exist)
POD_NAMESPACE = "airflow"


# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}
CWL_WORKFLOW = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/sbg/demos/aws-cli.cwl"

dag = DAG(
    dag_id="aws-cli-cwl-dag",
    description="AWS CLI Workflow as CWL",
    tags=["Unity", "SPS", "NASA", "JPL"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=1,
    default_args=dag_default_args,
    params={"cwl_workflow": Param(CWL_WORKFLOW, type="string")},
)

# Task that executes the specific CWL workflow with the previous arguments
cwl_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    name="aws-cli-cwl",
    on_finish_action="delete_pod",
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="aws-cli-cwl",
    full_pod_spec=k8s.V1Pod(k8s.V1ObjectMeta(name=("aws-cli-cwl-pod-" + uuid.uuid4().hex))),
    pod_template_file=POD_TEMPLATE_FILE,
    # resources={"request_memory": "512Mi", "limit_memory": "1024Mi"},
    dag=dag,
)

cwl_task
