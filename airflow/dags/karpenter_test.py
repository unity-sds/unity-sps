from datetime import datetime

from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

from airflow import DAG

default_args = {
    "owner": "unity-sps",
    "start_date": datetime.fromtimestamp(0),
}


dag = DAG(
    "kubernetes_tasks_with_affinity",
    default_args=default_args,
    description="DAG with Kubernetes Pod Operators using affinity configurations.",
    schedule=None,
    is_paused_upon_creation=False,
    tags=["test"],
)

# Define KubernetesPodOperator tasks with default affinity
compute_task = KubernetesPodOperator(
    namespace="default",
    image="hello-world",
    name="compute-task",
    task_id="compute_task",
    get_logs=True,
    dag=dag,
    is_delete_operator_pod=True,
    affinity={
        "preferredDuringSchedulingIgnoredDuringExecution": [
            {
                "weight": 1,
                "preference": {
                    "matchExpressions": [
                        {
                            "key": "capacity-type",
                            "operator": "In",
                            "values": "{{ dag_run.conf['tasks']['compute_task'].get('capacity_type', ['spot']) }}",
                        }
                    ]
                },
            }
        ],
        "requiredDuringSchedulingIgnoredDuringExecution": [
            {
                "nodeSelectorTerms": [
                    {
                        "matchExpressions": [
                            {
                                "key": "karpenter.k8s.aws/instance-category",
                                "operator": "In",
                                "values": "{{ dag_run.conf['tasks']['compute_task'].get('instance_category', ['c']) }}",
                            },
                            {
                                "key": "karpenter.k8s.aws/instance-cpu",
                                "operator": "In",
                                "values": "{{ dag_run.conf['tasks']['compute_task'].get('instance_cpu', ['8', '16']) }}",
                            },
                        ]
                    }
                ]
            }
        ],
    },
)

memory_task = KubernetesPodOperator(
    namespace="default",
    image="hello-world",
    name="memory-task",
    task_id="memory_task",
    get_logs=True,
    dag=dag,
    is_delete_operator_pod=True,
    affinity={
        "preferredDuringSchedulingIgnoredDuringExecution": [
            {
                "weight": 1,
                "preference": {
                    "matchExpressions": [
                        {
                            "key": "capacity-type",
                            "operator": "In",
                            "values": "{{ dag_run.conf['tasks']['memory_task'].get('capacity_type', ['spot']) }}",
                        }
                    ]
                },
            }
        ],
        "requiredDuringSchedulingIgnoredDuringExecution": [
            {
                "nodeSelectorTerms": [
                    {
                        "matchExpressions": [
                            {
                                "key": "karpenter.k8s.aws/instance-category",
                                "operator": "In",
                                "values": "{{ dag_run.conf['tasks']['memory_task'].get('instance_category', ['r']) }}",
                            },
                            {
                                "key": "karpenter.k8s.aws/instance-cpu",
                                "operator": "In",
                                "values": "{{ dag_run.conf['tasks']['memory_task'].get('instance_cpu', ['8', '16']) }}",
                            },
                        ]
                    }
                ]
            }
        ],
    },
)

general_task = KubernetesPodOperator(
    namespace="default",
    image="hello-world",
    name="general-task",
    task_id="general_task",
    get_logs=True,
    dag=dag,
    is_delete_operator_pod=True,
    affinity={
        "preferredDuringSchedulingIgnoredDuringExecution": [
            {
                "weight": 1,
                "preference": {
                    "matchExpressions": [
                        {
                            "key": "capacity-type",
                            "operator": "In",
                            "values": "{{ dag_run.conf['tasks']['general_task'].get('capacity_type', ['spot']) }}",
                        }
                    ]
                },
            }
        ],
        "requiredDuringSchedulingIgnoredDuringExecution": [
            {
                "nodeSelectorTerms": [
                    {
                        "matchExpressions": [
                            {
                                "key": "karpenter.k8s.aws/instance-category",
                                "operator": "In",
                                "values": "{{ dag_run.conf['tasks']['general_task'].get('instance_category', ['m']) }}",
                            },
                            {
                                "key": "karpenter.k8s.aws/instance-cpu",
                                "operator": "In",
                                "values": "{{ dag_run.conf['tasks']['general_task'].get('instance_cpu', ['8', '16']) }}",
                            },
                        ]
                    }
                ]
            }
        ],
    },
)

# Task sequence
compute_task >> memory_task >> general_task
