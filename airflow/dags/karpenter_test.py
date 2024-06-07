from datetime import datetime

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

POD_NAMESPACE = "airflow"
POD_LABEL = "karpenter_test_task"

default_args = {
    "owner": "unity-sps",
    "start_date": datetime.fromtimestamp(0),
}

default_params = {"placeholder": 1}


def get_affinity(
    capacity_type: list[str], instance_family=list[str], instance_cpu=list[str], anti_affinity_label=str
):

    affinity = {
        "nodeAffinity": {
            "preferredDuringSchedulingIgnoredDuringExecution": [
                {
                    "weight": 1,
                    "preference": {
                        "matchExpressions": [
                            {
                                "key": "karpenter.sh/capacity-type",
                                "operator": "In",
                                "values": capacity_type,
                            }
                        ]
                    },
                }
            ],
            "requiredDuringSchedulingIgnoredDuringExecution": {
                "nodeSelectorTerms": [
                    {
                        "matchExpressions": [
                            {
                                "key": "karpenter.k8s.aws/instance-family",
                                "operator": "In",
                                "values": instance_family,
                            },
                            {
                                "key": "karpenter.k8s.aws/instance-cpu",
                                "operator": "In",
                                "values": instance_cpu,
                            },
                        ]
                    }
                ]
            },
        },
        "podAntiAffinity": {
            "requiredDuringSchedulingIgnoredDuringExecution": [
                {
                    "labelSelector": {
                        "matchExpressions": [
                            {
                                "key": "app",
                                "operator": "In",
                                "values": [anti_affinity_label],
                            },
                        ]
                    },
                    "topologyKey": "kubernetes.io/hostname",
                }
            ]
        },
    }
    return affinity


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
        capacity_type=["spot"],
        instance_family=["c6i", "c5"],
        instance_cpu=["2", "4"],
        anti_affinity_label=POD_LABEL,
    ),
)

memory_task = KubernetesPodOperator(
    dag=dag,
    task_id="memory_task",
    namespace=POD_NAMESPACE,
    name="memory-task",
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
        capacity_type=["spot"],
        instance_family=["r6i", "r5"],
        instance_cpu=["2", "4"],
        anti_affinity_label=POD_LABEL,
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
        capacity_type=["spot"],
        instance_family=["m6i", "m5"],
        instance_cpu=["2", "4"],
        anti_affinity_label=POD_LABEL,
    ),
)

# Task sequence
compute_task >> memory_task >> general_task
