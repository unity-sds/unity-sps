# This test executes the specified CWL workflow
# using the CWL DAG submitted through the Airflow API.
# The workflow parameters are contained in a YAML file which is venue-dependent.
# The CWL DAG must already be deployed in Airflow,
# and it is invoked via the Airflow API.
# The CWL task is executed via a KubernetesPodOperator on a worker node
# that is dynamically provisioned by Karpenter.
from pathlib import Path

import backoff
import requests
from pytest_bdd import given, parsers, scenario, then, when

FILE_PATH = Path(__file__)
FEATURES_DIR = FILE_PATH.parent.parent / "features"
FEATURE_FILE: Path = FEATURES_DIR / "cwl_workflows_with_airflow_api.feature"

# DAG parameters are venue specific
DAG_ID = "cwl_dag"
DAG_PARAMETERS = {
    "EMIT": {
        "cwl_workflow": "http://awslbdockstorestack-lb-1429770210.us-west-2.elb.amazonaws.com:9998/api/ga4gh/trs/v2/tools/%23workflow%2Fdockstore.org%2FGodwinShen%2Femit-ghg/versions/9/plain-CWL/descriptor/workflow.cwl",
        "cwl_args": {
            "dev": "https://raw.githubusercontent.com/GodwinShen/emit-ghg/refs/heads/main"
            "/test/emit-ghg-dev.json",
            # "test": "https://raw.githubusercontent.com/GodwinShen/emit-ghg/refs/heads/main"
            # "/test/emit-ghg-test.json",
        },
        "request_memory": "16Gi",
        "request_cpu": "8",
        "request_storage": "100Gi",
        "use_ecr": False,
    },
    "SBG_E2E_SCALE": {
        "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/"
        "refs/heads/main/L1-to-L2-e2e.cwl",
        "cwl_args": {
            "dev": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/"
            "refs/heads/main/L1-to-L2-e2e.dev.yml",
        },
        "request_memory": "64Gi",
        "request_cpu": "32",
        "request_storage": "100Gi",
        "use_ecr": False,
    },
    "SBG_PREPROCESS": {
        "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main"
        "/preprocess/sbg-preprocess-workflow.cwl",
        "cwl_args": {
            "dev": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess"
            "/sbg-preprocess-workflow.dev.yml",
            "test": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess"
            "/sbg-preprocess-workflow.test.yml",
        },
        # r7i.xlarge (4 CPU, 32 GiB memory)
        "request_memory": "4Gi",
        "request_cpu": "2",
        "request_storage": "10Gi",
        "use_ecr": False,
    },
}


@scenario(FEATURE_FILE, "Successful execution of a CWL workflow with the Airflow API")
def test_successful_execution_of_a_cwl_workflow_with_the_airflow_api():
    pass


@given("the Airflow API is up and running")
def api_up_and_running():
    pass


@when(parsers.parse("I trigger a dag run for the {test_case} workflow"), target_fixture="response")
def trigger_dag(airflow_api_url, airflow_api_auth, venue, test_case):

    # check that this test_case is enabled for the specified venue
    if venue in DAG_PARAMETERS[test_case]["cwl_args"]:
        # DAG parameters are venue dependent
        cwl_workflow = DAG_PARAMETERS[test_case]["cwl_workflow"]
        cwl_args = DAG_PARAMETERS[test_case]["cwl_args"][venue]
        request_memory = DAG_PARAMETERS[test_case]["request_memory"]
        request_cpu = DAG_PARAMETERS[test_case]["request_cpu"]
        request_storage = DAG_PARAMETERS[test_case]["request_storage"]
        use_ecr = DAG_PARAMETERS[test_case]["use_ecr"]
        response = requests.post(
            f"{airflow_api_url}/api/v1/dags/{DAG_ID}/dagRuns",
            auth=airflow_api_auth,
            json={
                "conf": {
                    "cwl_workflow": f"{cwl_workflow}",
                    "cwl_args": f"{cwl_args}",
                    "request_memory": f"{request_memory}",
                    "request_cpu": f"{request_cpu}",
                    "request_storage": f"{request_storage}",
                    "use_ecr": use_ecr,
                }
            },
            # nosec
            verify=False,
        )
        return response
    else:
        print(f"Test case: {test_case} is NOT enabled for venue: {venue}, skipping")
        return None


@then("I receive a response with status code 200")
def check_status_code(response):
    if response is not None:
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"
    else:
        pass


def check_failed(e):
    if isinstance(e, AssertionError):
        return "failed" in e.args[0]
    return False


@then("I see an eventual successful dag run")
@backoff.on_exception(
    backoff.constant,
    (AssertionError, requests.exceptions.HTTPError),
    max_time=3600,
    giveup=check_failed,
    jitter=None,
    interval=5,
)
def poll_dag_run(response, airflow_api_url, airflow_api_auth):
    if response is not None:
        dag_json = response.json()
        dag_run_response = requests.get(
            f"""{airflow_api_url}/api/v1/dags/{dag_json["dag_id"]}/dagRuns/{dag_json["dag_run_id"]}""",
            auth=airflow_api_auth,
            # nosec
            verify=False,
        )
        assert dag_run_response.status_code == 200, (
            f"Expected status code 2" f"00, but got {response.status_code}"
        )
        json = dag_run_response.json()
        assert "state" in json, 'Expected "state" element in response'
        assert json["state"] == "success"
    else:
        pass
