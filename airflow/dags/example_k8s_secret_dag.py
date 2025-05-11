from datetime import timedelta

from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from airflow.providers.cncf.kubernetes.secret import Secret
from airflow.utils.dates import days_ago

from airflow import DAG

# Define the secret to mount as an environment variable
secret_env = Secret(
    deploy_type="env",  # or 'volume'
    deploy_target="MY_ENV_VAR",  # environment variable name
    secret="my-secret",  # name of the Kubernetes secret
    key="MY_ENV_VAR",  # key in the secret
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "example_k8s_secret_dag",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False,
) as dag:

    k8s_task = KubernetesPodOperator(
        task_id="run_with_secret",
        name="example-pod",
        namespace="sps",
        image="python:3.9-slim",
        cmds=["python", "-c"],
        arguments=['import os; print("Secret:", os.getenv("MY_ENV_VAR"))'],
        secrets=[secret_env],  # Inject secret
        is_delete_operator_pod=True,
        service_account_name="airflow-worker",
        in_cluster=True,
        get_logs=True,
        container_security_context={"privileged": True},
    )
