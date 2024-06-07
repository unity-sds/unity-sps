from datetime import datetime

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

POD_NAMESPACE = "airflow"

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
    labels={"app": "kubernetes_tasks_with_affinity"},
    annotations={"karpenter.sh/do-not-disrupt": "true"},
    affinity={
        "nodeAffinity": {
            "preferredDuringSchedulingIgnoredDuringExecution": [
                {
                    "weight": 1,
                    "preference": {
                        "matchExpressions": [
                            {
                                "key": "karpenter.sh/capacity-type",
                                "operator": "In",
                                "values": ["spot"],
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
                                "values": ["c6i", "c5"],
                            },
                            {
                                "key": "karpenter.k8s.aws/instance-cpu",
                                "operator": "In",
                                "values": ["2", "4"],
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
                                "values": ["kubernetes_tasks_with_affinity"],
                            },
                        ]
                    },
                    "topologyKey": "kubernetes.io/hostname",
                }
            ]
        },
    },
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
    labels={"app": "kubernetes_tasks_with_affinity"},
    annotations={"karpenter.sh/do-not-disrupt": "true"},
    affinity={
        "nodeAffinity": {
            "preferredDuringSchedulingIgnoredDuringExecution": [
                {
                    "weight": 1,
                    "preference": {
                        "matchExpressions": [
                            {
                                "key": "karpenter.sh/capacity-type",
                                "operator": "In",
                                "values": ["spot"],
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
                                "values": ["r6i", "r5"],
                            },
                            {
                                "key": "karpenter.k8s.aws/instance-cpu",
                                "operator": "In",
                                "values": ["2", "4"],
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
                                "values": ["kubernetes_tasks_with_affinity"],
                            },
                        ]
                    },
                    "topologyKey": "kubernetes.io/hostname",
                }
            ]
        },
    },
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
    labels={"app": "kubernetes_tasks_with_affinity"},
    annotations={"karpenter.sh/do-not-disrupt": "true"},
    affinity={
        "nodeAffinity": {
            "preferredDuringSchedulingIgnoredDuringExecution": [
                {
                    "weight": 1,
                    "preference": {
                        "matchExpressions": [
                            {
                                "key": "karpenter.sh/capacity-type",
                                "operator": "In",
                                "values": ["spot"],
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
                                "values": ["m6i", "m5"],
                            },
                            {
                                "key": "karpenter.k8s.aws/instance-cpu",
                                "operator": "In",
                                "values": ["2", "4"],
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
                                "values": ["kubernetes_tasks_with_affinity"],
                            },
                        ]
                    },
                    "topologyKey": "kubernetes.io/hostname",
                }
            ]
        },
    },
)

# Task sequence
compute_task >> memory_task >> general_task
