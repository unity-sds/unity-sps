import logging
import os
import shutil
from datetime import datetime

from airflow.models.baseoperator import chain
from airflow.operators.python import PythonOperator, get_current_context
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.utils.trigger_rule import TriggerRule
from kubernetes.client import models as k8s
from unity_sps_utils import get_affinity

from airflow import DAG

POD_NAMESPACE = "airflow"
POD_LABEL = "edrgen_task"
DOCKER_IMAGE = "ghcr.io/unity-sds/unity-sps/srl-idps-edrgen:develop"

# Persistent Volume SCRATCH_DIR is mounted as SHARED_DIR
SCRATCH_DIR = "/scratch"
SHARED_DIR = "/shared-task-data"

# FIXME: input filenames must be provided by the initiator
INPUT_EMD = "0980_0734432789-43133-1.emd"
INPUT_DAT = "0980_0734432789-43133-1.dat"


def get_working_dir(context):
    context = get_current_context()
    dag_run_id = context["dag_run"].run_id
    local_dir = f"{SHARED_DIR}/{dag_run_id}"
    return local_dir


# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}

dag = DAG(
    dag_id="edrgen_dag",
    description="EDRGen DAG",
    tags=["EDRGen"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=10,
    max_active_tasks=30,
    default_args=dag_default_args,
)


def setup(ti=None, **context):
    """
    Task that creates the working directory on the shared volume.
    """

    local_dir = get_working_dir(context)
    logging.info(f"Creating directory: {local_dir}")
    os.makedirs(local_dir, exist_ok=True)
    logging.info(f"Created directory: {local_dir}")


setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)


def stage_in(ti=None, **context):
    """
    Copies the input files to the working directory
    shared across all Tasks in this DAG run.
    """

    local_dir = get_working_dir(context)
    shutil.copyfile(f"{SHARED_DIR}/edrgen_inputs/{INPUT_EMD}", f"{local_dir}/{INPUT_EMD}")
    shutil.copyfile(f"{SHARED_DIR}/edrgen_inputs/{INPUT_DAT}", f"{local_dir}/{INPUT_DAT}")
    dir_list = os.listdir(local_dir)
    logging.info(dir_list)


stage_in_task = PythonOperator(task_id="StageIn", python_callable=stage_in, dag=dag)

# see KPO templated fields: https://github.com/apache/airflow/blob/fcfc7f12421bd35a366324fe7814c90da8de5735/airflow/providers/cncf/kubernetes/operators/kubernetes_pod.py#L145
process_task = KubernetesPodOperator(
    retries=0,
    task_id="process_task",
    namespace=POD_NAMESPACE,
    name="edrgen-pod",
    image=DOCKER_IMAGE,
    service_account_name="airflow-worker",
    in_cluster=True,
    get_logs=True,
    startup_timeout_seconds=1800,
    arguments=[
        f"{SHARED_DIR}/" + "{{ dag_run.run_id }}" + f"/{INPUT_DAT}",
        f"{SHARED_DIR}/" + "{{ dag_run.run_id }}" + f"/{INPUT_EMD}",
        f"{SHARED_DIR}/" + "{{ dag_run.run_id }}",
    ],
    container_security_context={"privileged": True},
    # container_resources=CONTAINER_RESOURCES,
    container_logs=True,
    volume_mounts=[
        k8s.V1VolumeMount(name="workers-volume", mount_path=SCRATCH_DIR, sub_path="{{ dag_run.run_id }}")
    ],
    volumes=[
        k8s.V1Volume(
            name="workers-volume",
            persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="airflow-kpo"),
        )
    ],
    dag=dag,
    node_selector={"karpenter.sh/nodepool": "airflow-kubernetes-pod-operator"},
    labels={"app": POD_LABEL},
    annotations={"karpenter.sh/do-not-disrupt": "true"},
    # r7i.xlarge: 4 vCPUs, 32 GiB memory
    affinity=get_affinity(
        capacity_type=["spot"],
        instance_type=["r7i.xlarge"],
        anti_affinity_label=POD_LABEL,
    ),
    on_finish_action="keep_pod",
    is_delete_operator_pod=False,
)


def stage_out(ti=None, **context):
    """
    Copies the output products from the working directory to their final location.
    """
    logging.info("Staging out products")


stage_out_task = PythonOperator(task_id="StageOut", python_callable=stage_out, dag=dag)


def cleanup(**context):
    """
    Tasks that deletes all data shared between Tasks
    from the Kubernetes PersistentVolume
    """

    local_dir = get_working_dir(context)
    if os.path.exists(local_dir):
        shutil.rmtree(local_dir)
        logging.info(f"Deleted directory: {local_dir}")
    else:
        logging.info(f"Directory does not exist, no need to delete: {local_dir}")


cleanup_task = PythonOperator(
    task_id="Cleanup", python_callable=cleanup, dag=dag, trigger_rule=TriggerRule.ALL_DONE
)

chain(setup_task, stage_in_task, process_task, stage_out_task, cleanup_task)
