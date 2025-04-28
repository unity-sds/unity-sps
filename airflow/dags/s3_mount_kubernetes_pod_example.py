from airflow.models.baseoperator import chain
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from kubernetes.client import models as k8s

from airflow import DAG

# Use a Docker image that has access to S3 (and has bash or Python)
DOCKER_IMAGE = "amazonlinux:2"

with DAG(
    dag_id="s3_mount_kubernetes_pod_example",
    schedule_interval=None,
    catchup=False,
    schedule=None,
) as dag:

    # Define the volume using a pre-created PVC that mounts S3
    volume = k8s.V1Volume(
        name="s3-mount-volume",
        persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="s3-pvc"),
    )

    # Define how the volume is mounted inside the pod
    volume_mount = k8s.V1VolumeMount(
        name="s3-mount-volume", mount_path="/mnt/s3", read_only=False  # Path inside the container
    )

    write_task = KubernetesPodOperator(
        task_id="write_s3_from_pod",
        name="s3-write-task",
        namespace="sps",
        image=DOCKER_IMAGE,
        cmds=["sh", "-c"],
        arguments=["echo 'Hello from the container!' >> /mnt/s3/$(date -u).txt"],
        volumes=[volume],
        volume_mounts=[volume_mount],
        get_logs=True,
        is_delete_operator_pod=True,
        service_account_name="airflow-worker",
        startup_timeout_seconds=1800,
        container_security_context={"privileged": True},
        owner="unity-sps",
        node_selector={"karpenter.sh/nodepool": "airflow-kubernetes-pod-operator"},
        annotations={"karpenter.sh/do-not-disrupt": "true"},
    )

    list_task = KubernetesPodOperator(
        task_id="list_s3_from_pod",
        name="s3-list-task",
        namespace="sps",
        image=DOCKER_IMAGE,
        cmds=["sh", "-c"],
        arguments=["ls /mnt/s3"],  # just listing contents for demo
        volumes=[volume],
        volume_mounts=[volume_mount],
        get_logs=True,
        is_delete_operator_pod=True,
        service_account_name="airflow-worker",
        startup_timeout_seconds=1800,
        container_security_context={"privileged": True},
        owner="unity-sps",
        node_selector={"karpenter.sh/nodepool": "airflow-kubernetes-pod-operator"},
        annotations={"karpenter.sh/do-not-disrupt": "true"},
    )

    chain(write_task, list_task)
