# Test DAG that used CWL to invoke the busybox Docker image

import json
import uuid
from datetime import datetime

from airflow.models.param import Param
from airflow.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from kubernetes.client import models as k8s

from airflow import DAG

# The Kubernetes Pod that executes the CWL-Docker container
# Must use elevated privileges to start/stop the Docker engine
POD_TEMPLATE_FILE = "/opt/airflow/dags/docker_cwl_pod.yaml"

# The Kubernetes namespace within which the Pod is run (it must already exist)
POD_NAMESPACE = "airflow"

# The path of the working directory where the CWL workflow is executed
# (aka the starting directory for cwl-runner).
# This is fixed to the EFS /scratch directory in this DAG.
WORKING_DIR = "/scratch"

# Default DAG configuration
dag_default_args = {
    "owner": "unity-sps",
    "depends_on_past": False,
    "start_date": datetime.utcfromtimestamp(0),
}

dag = DAG(
    dag_id="busybox",
    description="Test DAG using busybox",
    tags=["Test"],
    is_paused_upon_creation=False,
    catchup=False,
    schedule=None,
    max_active_runs=100,
    default_args=dag_default_args,
    params={"message": Param('"Hello World"', type="string")},
)


# This Task creates dictionaries of data that is passed via Xcom to the downstream Tasks
def setup(ti=None, **context):

    echo_message_dict = {
        "message": context["params"]["message"],
    }
    ti.xcom_push(key="echo_message_args", value=json.dumps(echo_message_dict))

    cat_file_dict = {"the_file": {"class": "File", "path": "echo_message.txt"}}
    ti.xcom_push(key="cat_file_args", value=json.dumps(cat_file_dict))


setup_task = PythonOperator(task_id="Setup", python_callable=setup, dag=dag)


# This Task executes a CWL workflow that invokes the busybox Docker container.
# to write a file in the shared '/scratch' directory.
# It also includes an example on how to set limits on the resources used by the Pod.
ECHO_MESSAGE_CWL = (
    "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/main/demos/echo_message.cwl"
)
echo_message_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    name="Echo_Message",
    on_finish_action="delete_pod",
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="Echo_Message",
    full_pod_spec=k8s.V1Pod(k8s.V1ObjectMeta(name=("echo-message-pod-" + uuid.uuid4().hex))),
    pod_template_file=POD_TEMPLATE_FILE,
    container_resources=k8s.V1ResourceRequirements(
        limits={"memory": "250M", "cpu": "100m", "ephemeral-storage": "5G"},
        requests={"ephemeral-storage": "5G"},
    ),
    arguments=[ECHO_MESSAGE_CWL, "{{ti.xcom_pull(task_ids='Setup', key='echo_message_args')}}"],
    volume_mounts=[
        k8s.V1VolumeMount(name="workers-volume", mount_path=WORKING_DIR, sub_path="{{ dag_run.run_id }}")
    ],
    volumes=[
        k8s.V1Volume(
            name="workers-volume",
            persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="kpo-efs"),
        )
    ],
    dag=dag,
)

# This Task reads the file written to the '/scratch' directory by the upstream Task.
# IMPORTANT: the "cat_file.cwl" MUST stage the input file to the working directory inside the Docker container
# before the busybox Docker container can read it.
# This Task also passes an additional optional parameter to the Pod to store the content of the
# file "cat_file.txt" into Xcom so that it can be retrieved by the downstream Tasks.
CAT_FILE_CWL = "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/main/demos/cat_file.cwl"
cat_file_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    name="Cat_File",
    on_finish_action="delete_pod",
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="Cat_File",
    full_pod_spec=k8s.V1Pod(k8s.V1ObjectMeta(name=("cat_file-pod-" + uuid.uuid4().hex))),
    pod_template_file=POD_TEMPLATE_FILE,
    arguments=[CAT_FILE_CWL, "{{ti.xcom_pull(task_ids='Setup', key='cat_file_args')}}", "cat_file.txt"],
    volume_mounts=[
        k8s.V1VolumeMount(name="workers-volume", mount_path=WORKING_DIR, sub_path="{{ dag_run.run_id }}")
    ],
    volumes=[
        k8s.V1Volume(
            name="workers-volume",
            persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="kpo-efs"),
        )
    ],
    dag=dag,
    do_xcom_push=True,
)

# This Task is an example on how to retrieve the Xcom data pushed by an upstream KubernetesPodOperator.
echo_xcom_task = KubernetesPodOperator(
    namespace=POD_NAMESPACE,
    name="Echo_Xcom",
    on_finish_action="delete_pod",
    hostnetwork=False,
    startup_timeout_seconds=1000,
    get_logs=True,
    task_id="Echo_Xcom",
    full_pod_spec=k8s.V1Pod(k8s.V1ObjectMeta(name=("echo-xcom-pod-" + uuid.uuid4().hex))),
    pod_template_file=POD_TEMPLATE_FILE,
    arguments=[ECHO_MESSAGE_CWL, '{"message": "{{ ti.xcom_pull(\'Cat_File\') }}" }'],
    volume_mounts=[
        k8s.V1VolumeMount(name="workers-volume", mount_path=WORKING_DIR, sub_path="{{ dag_run.run_id }}")
    ],
    volumes=[
        k8s.V1Volume(
            name="workers-volume",
            persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="kpo-efs"),
        )
    ],
    dag=dag,
)

setup_task >> echo_message_task >> cat_file_task >> echo_xcom_task
