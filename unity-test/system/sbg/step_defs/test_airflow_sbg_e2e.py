from datetime import datetime, timezone
from pathlib import Path

import requests
import backoff
from pytest_bdd import given, scenario, then, when

FILE_PATH = Path(__file__)
FEATURES_DIR = FILE_PATH.parent.parent / "features"
FEATURE_FILE = FEATURES_DIR / "airflow_sbg_e2e.feature"


@scenario(FEATURE_FILE, "Check SBG E2E processing")
def test_check_sbg_e2e():
    pass


@given("the Airflow API is up and running")
def api_up_and_running():
    pass


@when("I trigger a dag run for the SBG E2E dag", target_fixture="response")
def trigger_dag(airflow_api_url, airflow_api_auth):
    # leaving out dag_run_id to avoid conflicts with previous runs- we can always fetch it from the response
    # unsure about contents of the conf argument, though
    response = requests.post(f"{airflow_api_url}/api/v1/dags/sbg-l1-to-l2-e2e-cwl-step-by-step-dag/dagRuns",
                             auth = airflow_api_auth, json={ "note":"Triggered by unity-test suite"})
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
    dag_run_response = requests.get(f"""{airflow_api_url}/api/v1/dags/{dag_json["dag_id"]}/dagRuns/{dag_json["dag_run_id"]}""",
                                    auth = airflow_api_auth)
    assert dag_run_response.status_code == 200, f"Expected status code 200, but got {response.status_code}"
    json = dag_run_response.json()
    assert "state" in json, "Expected \"state\" element in response"
    assert json["state"] == "success"

