# This test executes the specified CWL workflow
# using the CWL DAG OGC process submitted through the OGC API.
# The workflow parameters are contained in a YAML file which is venue-dependent.
# The CWL DAG OGC process must already be deployed in Airflow,
# and it is invoked via the OGC API.
# The CWL task is executed via a KubernetesPodOperator on a worker node
# that is dynamically provisioned by Karpenter.
import json
from pathlib import Path

import backoff
from pytest_bdd import given, parsers, scenario, then, when
from unity_sds_client.resources.job_status import JobStatus
from unity_sds_client.unity_exception import UnityException
from unity_sps_ogc_processes_api_python_client.exceptions import ApiException, ServiceException

FILE_PATH = Path(__file__)
FEATURES_DIR = FILE_PATH.parent.parent / "features"
FEATURE_FILE: Path = FEATURES_DIR / "cwl_workflows_with_ogc_api.feature"

# DAG parameters are venue specific
CWL_DAG_ID = "cwl_dag"
CWL_DAG_MODULAR_ID = "cwl_dag_modular"
CWL_DAG_DATA = {
    "EMIT": {
        "inputs": {
            "cwl_workflow": "http://awslbdockstorestack-lb-1429770210.us-west-2.elb.amazonaws.com:9998/api/ga4gh/trs/v2/tools/%23workflow%2Fdockstore.org%2FGodwinShen%2Femit-ghg/versions/9/plain-CWL/descriptor/workflow.cwl",
            "cwl_args": {
                "dev": "https://raw.githubusercontent.com/GodwinShen/emit-ghg/refs/heads/main/test/emit-ghg-dev.json"
            },
            "log_level": "INFO",
            "request_storage": "100Gi",
            # r7i.2xlarge: 8 CPUs, 64 GB memory
            "request_instance_type": "r7i.2xlarge",
        },
        "outputs": {"result": {"transmissionMode": "reference"}},
    },
    "SBG_PREPROCESS": {
        "inputs": {
            "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main"
            "/preprocess/sbg-preprocess-workflow.cwl",
            "cwl_args": {
                "dev": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess"
                "/sbg-preprocess-workflow.dev.yml",
                "test": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess"
                "/sbg-preprocess-workflow.test.yml",
            },
            "log_level": "INFO",
            "request_storage": "10Gi",
            # c6i.xlarge: 4vCPUs, 8 GB memory
            # r7i.xlarge: 4 CPUs 32 GB memory
            "request_instance_type": "r7i.xlarge",
        },
        "outputs": {"result": {"transmissionMode": "reference"}},
    },
    "SBG_E2E_SCALE": {
        "inputs": {
            "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/"
            "sbg-workflows/refs/heads/main/L1-to-L2-e2e.cwl",
            "cwl_args": {
                "dev": "https://raw.githubusercontent.com/unity-sds/"
                "sbg-workflows/refs/heads/main/L1-to-L2-e2e.dev.yml",
            },
            "log_level": "INFO",
            "request_storage": "100Gi",
            # c6i.8xlarge: 32 CPUs, 64 GB memory
            "request_instance_type": "c6i.8xlarge",
        },
        "outputs": {"result": {"transmissionMode": "reference"}},
    },
}

CWL_DAG_MODULAR_DATA = {
    "EMIT": {
        "inputs": {
            "stac_json": "https://raw.githubusercontent.com/unity-sds/unity-tutorial-application/refs/heads/main/test/stage_in/stage_in_results.json",
            "process_workflow": "https://raw.githubusercontent.com/mike-gangl/unity-OGC-example-application/refs/heads/main/process.cwl",
            "process_args": json.dumps({"example_argument_empty": ""}),
            "log_level": "INFO",
            "request_instance_type": "t3.medium",
            "request_storage": "10Gi",
        },
        "outputs": {"result": {"transmissionMode": "reference"}},
    },
    "SBG_PREPROCESS": {
        "inputs": {
            "stac_json": "https://raw.githubusercontent.com/brianlee731/SBG-unity-preprocess-mod/refs/heads/main/test/stage-in/featureCollection.json",
            "process_workflow": "http://awslbdockstorestack-lb-1429770210.us-west-2.elb.amazonaws.com:9998/api/ga4gh/trs/v2/tools/%23workflow%2Fdockstore.org%2Fedwinsarkissian%2FSBG-unity-preprocess-mod/versions/4/PLAIN-CWL/descriptor/%2Fprocess.cwl",
            "process_args": json.dumps({}),
            "log_level": "INFO",
            "request_instance_type": "t3.2xlarge",
            "request_storage": "100Gi",
        },
        "outputs": {"result": {"transmissionMode": "reference"}},
    },
    "SBG_ISOFIT": {
        "inputs": {
            "stac_json": "https://raw.githubusercontent.com/brianlee731/SBG-unity-isofit-mod_test/refs/heads/main/test/catalog.json",
            "process_workflow": "http://awslbdockstorestack-lb-1429770210.us-west-2.elb.amazonaws.com:9998/api/ga4gh/trs/v2/tools/%23workflow%2Fdockstore.org%2Fbrianlee731%2FSBG-unity-isofit-mod_test/versions/14/PLAIN-CWL/descriptor/%2Fprocess.cwl",
            "process_args": json.dumps({}),
            "log_level": "INFO",
            "request_instance_type": "r7i.2xlarge",
            "request_storage": "100Gi",
        },
        "outputs": {"result": {"transmissionMode": "reference"}},
    },
}


@scenario(FEATURE_FILE, "Successful execution of a CWL workflow with the OGC API")
def test_successful_execution_of_a_cwl_workflow_with_the_ogc_api():
    pass


@given("the OGC API is up and running")
def api_up_and_running(ogc_processes):
    assert ogc_processes is not None and len(ogc_processes) > 0


@when(parsers.parse("I trigger a {test_case} OGC job for the {test_dag} OGC process"), target_fixture="job")
def trigger_process(cwl_dag_process, cwl_dag_modular_process, venue, test_case, test_dag):

    # check that this test_case and test_dag are enabled for the specified venue
    ogc_process = None
    payload = None
    try:

        if test_dag == CWL_DAG_ID:
            ogc_process = cwl_dag_process
            payload = CWL_DAG_DATA[test_case]
            payload["inputs"]["cwl_args"] = payload["inputs"]["cwl_args"][venue]
        elif test_dag == CWL_DAG_MODULAR_ID:
            ogc_process = cwl_dag_modular_process
            payload = CWL_DAG_MODULAR_DATA[test_case]

        print(ogc_process)
        assert ogc_process is not None
        print(payload)
        assert payload is not None

        # submit job
        job = ogc_process.execute(payload)
        assert job is not None
        return job

    except KeyError:
        print(f"Test case: {test_case} and Test DAG: {test_dag} are NOT enabled for venue: {venue}")
        return None


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
            print(f"Job: {job.id} status: {job.get_status().status}")
            status = job.get_status().status

        print(f"Job: {job.id} status: {job.get_status().status}")
        assert job.get_status().status == JobStatus.SUCCESSFUL
    else:
        pass
