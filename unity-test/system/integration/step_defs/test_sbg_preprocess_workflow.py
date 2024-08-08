# This test executes the SBG Preprocess DAG as a CWL workflow.
# The workflow parameters are contained in a YAML file which is venue-dependent.
# The SBG Preprocess DAG must already be deployed in Airflow,
# and it is invoked via the Airflow API.
# The CWL task is executed via a KubernetesPodOperator on a worker node
# that is dynamically provisioned by Karpenter.
from pathlib import Path

import backoff
import requests
from pytest_bdd import given, scenario, then, when

FILE_PATH = Path(__file__)
FEATURES_DIR = FILE_PATH.parent.parent / "features"
FEATURE_FILE: Path = FEATURES_DIR / "sbg_preprocess_workflow.feature"

# DAG parameters are venue specific
DAG_ID = "sbg_preprocess_cwl_dag"
SBG_PREPROCESS_PARAMETERS = {
    "dev": {
        "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.cwl",
        "cwl_args": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.dev.yml",
    },
    "test": {
        "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.cwl",
        "cwl_args": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.test.yml",
    },
}


@scenario(FEATURE_FILE, "Check SBG Preprocess Workflow")
def test_check_sbg_preprocess_workflow():
    pass


@given("the Airflow API is up and running")
def api_up_and_running():
    pass


@when("I trigger a dag run for the SBG Preprocess dag", target_fixture="response")
def trigger_dag(airflow_api_url, airflow_api_auth, venue):
    # DAG parameters are venue dependent
    cwl_workflow = SBG_PREPROCESS_PARAMETERS[venue]["cwl_workflow"]
    cwl_args = SBG_PREPROCESS_PARAMETERS[venue]["cwl_args"]
    response = requests.post(
        f"{airflow_api_url}/api/v1/dags/{DAG_ID}/dagRuns",
        auth=airflow_api_auth,
        json={"conf": {"cwl_workflow": f"{cwl_workflow}", "cwl_args": f"{cwl_args}"}},
        # nosec
        verify=False,
    )
    return response


@then("I receive a response with status code 200")
def check_status_code(response):
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"


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
    interval=1,
)
def poll_dag_run(response, airflow_api_url, airflow_api_auth):
    dag_json = response.json()
    dag_run_response = requests.get(
        f"""{airflow_api_url}/api/v1/dags/{dag_json["dag_id"]}/dagRuns/{dag_json["dag_run_id"]}""",
        auth=airflow_api_auth,
        # nosec
        verify=False,
    )
    assert dag_run_response.status_code == 200, f"Expected status code 200, but got {response.status_code}"
    json = dag_run_response.json()
    assert "state" in json, 'Expected "state" element in response'
    assert json["state"] == "success"
