from datetime import datetime

from kubernetes.client import models as k8s
from unity_sps_utils import get_node_affinity

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

POD_NAMESPACE = "airflow"


CONTAINER_RESOURCES = k8s.V1ResourceRequirements(requests={"cpu": "3"})

default_args = {
    "owner": "unity-sps",
    "start_date": datetime.fromtimestamp(0),
}

default_params = {"placeholder": 1}


dag = DAG(
    "kubernetes_tasks_with_affinity",
    default_args=default_args,
    description="DAG with Kubernetes Pod Operators using affinity configurations.",
    schedule=None,
    is_paused_upon_creation=False,
    tags=["test"],
    params=default_params,
)

# Define KubernetesPodOperator tasks with default affinity
compute_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    image="busybox",
    cmds=["sleep"],
    arguments=["60"],
    name="compute-task",
    task_id="compute_task",
    get_logs=True,
    dag=dag,
    labels={"task-type": "standalone"},
    # on_finish_action="keep_pod",
    is_delete_operator_pod=False,
    # container_resources=CONTAINER_RESOURCES,
    node_selector={"karpenter.sh/nodepool": "airflow-kubernetes-pod-operator"},
    affinity=get_node_affinity(capacity_type=["spot"], instance_family=["c6i"], instance_cpu=["4"]),
    startup_timeout_seconds=1800,
)

memory_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    image="busybox",
    cmds=["sleep"],
    arguments=["60"],
    name="memory-task",
    task_id="memory_task",
    get_logs=True,
    dag=dag,
    labels={"task-type": "standalone"},
    # on_finish_action="keep_pod",
    is_delete_operator_pod=False,
    # container_resources=CONTAINER_RESOURCES,
    node_selector={"karpenter.sh/nodepool": "airflow-kubernetes-pod-operator"},
    affinity=get_node_affinity(capacity_type=["spot"], instance_family=["r6i"], instance_cpu=["4"]),
    startup_timeout_seconds=1800,
)

general_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    image="busybox",
    cmds=["sleep"],
    arguments=["60"],
    name="general-task",
    task_id="general_task",
    get_logs=True,
    dag=dag,
    labels={"task-type": "standalone"},
    # container_resources=CONTAINER_RESOURCES,
    # on_finish_action="keep_pod",
    is_delete_operator_pod=False,
    node_selector={"karpenter.sh/nodepool": "airflow-kubernetes-pod-operator"},
    affinity=get_node_affinity(capacity_type=["spot"], instance_family=["m6i"], instance_cpu=["4"]),
    startup_timeout_seconds=1800,
)

# Task sequence
compute_task >> memory_task >> general_task
