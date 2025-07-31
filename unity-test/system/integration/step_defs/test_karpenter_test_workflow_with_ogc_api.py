# This test uses the OGC API
# to execute the "Karpenter Test" workflow
# which is a DAG composed of 3 "dummy" tasks,
# each executing on a different node type.
# A successful test will confirm
# that the OGC API, Keda and Karpenter are working properly,
# for the given SPS deployment and venue.
from pathlib import Path

import backoff
from pytest_bdd import given, scenario, then, when
from unity_sds_client.resources.job_status import JobStatus
from unity_sds_client.unity_exception import UnityException
from unity_sps_ogc_processes_api_python_client.exceptions import ApiException, ServiceException

FILE_PATH = Path(__file__)
FEATURES_DIR = FILE_PATH.parent.parent / "features"
FEATURE_FILE: Path = FEATURES_DIR / "karpenter_test_workflow_with_ogc_api.feature"

# DAG parameters are venue specific
DAG_ID = "karpenter_test"
DAG_PARAMETERS = {"placeholder": 1}


@scenario(FEATURE_FILE, "Execute the Karpenter Test Workflow with the OGC API")
def test_execute_karpenter_test_workflow_with_the_ogc_api():
    pass


@given("the OGC API is up and running")
def api_up_and_running():
    pass


@when("I trigger a run for the Karpenter Test DAG using the OGC API", target_fixture="job")
def trigger_process(karpenter_dag_process):

    ogc_process = karpenter_dag_process
    payload = DAG_PARAMETERS

    # print(ogc_process)
    assert ogc_process is not None
    # print(payload)
    assert payload is not None

    # submit job
    job = ogc_process.execute(payload)
    assert job is not None
    return job


@then("the job starts executing")
def check_job_started(job):
    if job is not None:
        status = job.get_status().status
        assert status in [JobStatus.ACCEPTED, JobStatus.RUNNING]
    else:
        pass


def check_failed(e):
    if isinstance(e, AssertionError):
        return "failed" in e.args[0]
    return False


@then("I see an eventual successful job")
@backoff.on_exception(
    backoff.constant,
    (AssertionError, ApiException, ServiceException, UnityException),
    max_time=7200,
    giveup=check_failed,
    jitter=None,
    interval=5,
)
def check_process_execution_and_termination(job):

    if job is not None:
        status = job.get_status().status
        while status in [JobStatus.ACCEPTED, JobStatus.RUNNING]:
            # print(f"Job: {job.id} status: {job.get_status().status}")
            status = job.get_status().status

        print(f"Job: {job.id} status: {job.get_status().status}")
        assert job.get_status().status == JobStatus.SUCCESSFUL
    else:
        pass
