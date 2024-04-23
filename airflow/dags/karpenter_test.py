from datetime import datetime

from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

from airflow import DAG

POD_NAMESPACE = "airflow"

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
    image="hello-world",
    name="compute-task",
    task_id="compute_task",
    get_logs=True,
    dag=dag,
    is_delete_operator_pod=True,
    node_selector={"karpenter.sh/nodepool": "airflow-kubernetes-pod-operator"},
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
                            {"key": "karpenter.k8s.aws/instance-category", "operator": "In", "values": ["c"]},
                            {
                                "key": "karpenter.k8s.aws/instance-cpu",
                                "operator": "In",
                                "values": ["2", "4"],
                            },
                        ]
                    }
                ]
            },
        }
    },
    startup_timeout_seconds=900,
)

memory_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    image="hello-world",
    name="memory-task",
    task_id="memory_task",
    get_logs=True,
    dag=dag,
    is_delete_operator_pod=True,
    node_selector={"karpenter.sh/nodepool": "airflow-kubernetes-pod-operator"},
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
                            {"key": "karpenter.k8s.aws/instance-category", "operator": "In", "values": ["r"]},
                            {
                                "key": "karpenter.k8s.aws/instance-cpu",
                                "operator": "In",
                                "values": ["2", "4"],
                            },
                        ]
                    }
                ]
            },
        }
    },
    startup_timeout_seconds=900,
)

general_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    image="hello-world",
    name="general-task",
    task_id="general_task",
    get_logs=True,
    dag=dag,
    is_delete_operator_pod=True,
    node_selector={"karpenter.sh/nodepool": "airflow-kubernetes-pod-operator"},
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
                            {"key": "karpenter.k8s.aws/instance-category", "operator": "In", "values": ["m"]},
                            {
                                "key": "karpenter.k8s.aws/instance-cpu",
                                "operator": "In",
                                "values": ["2", "4"],
                            },
                        ]
                    }
                ]
            },
        }
    },
    startup_timeout_seconds=900,
)

# Task sequence
compute_task >> memory_task >> general_task
