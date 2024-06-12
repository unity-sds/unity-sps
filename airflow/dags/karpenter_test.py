from datetime import datetime

from unity_sps_utils import get_affinity

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

POD_NAMESPACE = "airflow"
POD_LABEL = "karpenter_test_task"

default_args = {
    "owner": "unity-sps",
    "start_date": datetime.fromtimestamp(0),
}

default_params = {"placeholder": 1}


dag = DAG(
    "karpenter_test",
    default_args=default_args,
    description="DAG with Kubernetes Pod Operators using affinity configurations.",
    schedule=None,
    is_paused_upon_creation=False,
    tags=["test"],
    params=default_params,
)

# Define KubernetesPodOperator tasks with default affinity
compute_task = KubernetesPodOperator(
    dag=dag,
    task_id="compute_task",
    namespace=POD_NAMESPACE,
    name="compute-task",
    image="busybox",
    cmds=["sleep"],
    arguments=["60"],
    retries=3,
    in_cluster=True,
    get_logs=True,
    container_logs=True,
    startup_timeout_seconds=900,
    node_selector={"karpenter.sh/nodepool": "airflow-kubernetes-pod-operator"},
    labels={"app": POD_LABEL},
    annotations={"karpenter.sh/do-not-disrupt": "true"},
    affinity=get_affinity(
        instance_type=["c6i.large", "c5.large"], capacity_type=["spot"], anti_affinity_label=POD_LABEL
    ),
)

memory_task = KubernetesPodOperator(
    dag=dag,
    task_id="memory_task",
    namespace=POD_NAMESPACE,
    name="memory-task",
    image="busybox",
    cmds=["sleep"],
    arguments=["10"],
    retries=3,
    in_cluster=True,
    get_logs=True,
    container_logs=True,
    startup_timeout_seconds=900,
    node_selector={"karpenter.sh/nodepool": "airflow-kubernetes-pod-operator"},
    labels={"app": POD_LABEL},
    annotations={"karpenter.sh/do-not-disrupt": "true"},
    affinity=get_affinity(
        instance_type=["r6i.large", "r5.large"], capacity_type=["spot"], anti_affinity_label=POD_LABEL
    ),
)


general_task = KubernetesPodOperator(
    dag=dag,
    task_id="general_task",
    namespace=POD_NAMESPACE,
    name="general-task",
    image="busybox",
    cmds=["sleep"],
    arguments=["60"],
    retries=3,
    in_cluster=True,
    get_logs=True,
    container_logs=True,
    startup_timeout_seconds=900,
    node_selector={"karpenter.sh/nodepool": "airflow-kubernetes-pod-operator"},
    labels={"app": POD_LABEL},
    annotations={"karpenter.sh/do-not-disrupt": "true"},
    affinity=get_affinity(
        instance_type=["m6i.large", "m5.large"], capacity_type=["spot"], anti_affinity_label=POD_LABEL
    ),
)

# Task sequence
compute_task >> memory_task >> general_task
