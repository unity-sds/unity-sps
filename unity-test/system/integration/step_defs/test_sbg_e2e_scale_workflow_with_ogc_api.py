# This test executes the SBG End-To-End Scale CWL workflow using the OGC API.
# The workflow parameters are contained in a YAML file which is venue-dependent.
# The CWL DAG must already be deployed in Airflow,
# and it is invoked via the OGC API.
# The CWL task is executed via a KubernetesPodOperator on a worker node
# that is dynamically provisioned by Karpenter.
from pathlib import Path

import backoff
import requests
from pytest_bdd import given, scenario, then, when

import os
import time

from unity_sds_client.unity import Unity
from unity_sds_client.unity_services import UnityServices
from unity_sds_client.resources.job_status import JobStatus
from unity_sds_client.unity import UnityEnvironments

FILE_PATH = Path(__file__)
FEATURES_DIR = FILE_PATH.parent.parent / "features"
FEATURE_FILE: Path = FEATURES_DIR / "sbg_e2e_scale_workflow_with_ogc_api.feature"

# DAG parameters are venue specific
DAG_ID = "cwl_dag"
DATA = {
  "inputs": {
    "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/L1-to-L2-e2e.scale.cwl",
    "cwl_args": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/L1-to-L2-e2e.dev.scale.yml",
    "request_memory": "64Gi",
    "request_cpu": "32",
    "request_storage": "100Gi",
    "use_ecr": True
  },
  "outputs": {
    "result": {
      "transmissionMode": "reference"
    }
  }
}


@scenario(FEATURE_FILE,
          "Successful execution of the SBG End-To-End Scale Workflow with the OGC API")
def test_successful_execution_of_sbg_e2e_scale_workflow_with_ogc_api():
    pass


@given("the OGC API is up and running")
def api_up_and_running(ogc_processes):

    assert ogc_processes is not None and len(ogc_processes) > 0


@when("I trigger a job for the SBG End-To-End Scale process", target_fixture="job")
def trigger_process(cwl_dag_process):

    print(cwl_dag_process)
    assert cwl_dag_process is not None

    job = cwl_dag_process.execute(DATA)
    assert job is not None
    return job

@then("The job starts executing")
def check_job_started(job):
    status = job.get_status().status
    assert status in [JobStatus.ACCEPTED, JobStatus.RUNNING]

def check_failed(e):
    if isinstance(e, AssertionError):
        return "failed" in e.args[0]
    return False


@then("I see an eventual successful job")
@backoff.on_exception(
    backoff.constant,
    (AssertionError, requests.exceptions.HTTPError),
    max_time=3600,
    giveup=check_failed,
    jitter=None,
    interval=5,
)
def check_process_execution_and_termination(job):

    status = job.get_status().status
    while status in [JobStatus.ACCEPTED, JobStatus.RUNNING]:
        print(f"Job: {job.id} status: {job.get_status().status}")
        status = job.get_status().status

    print(f"Job: {job.id} status: {job.get_status().status}")
    assert job.get_status().status == JobStatus.SUCCESSFUL
