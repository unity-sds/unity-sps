# This test uses the Airflow API
# to execute the "Karpenter Test" workflow
# which is a DAG composed of 3 "dummy" tasks,
# each executing on a different node type.
# A successful test will confirm
# that the Airflow API, Keda and Karpenter are working properly,
# for the given SPS deployment and venue.
from pathlib import Path

import backoff
import requests
from pytest_bdd import given, scenario, then, when

FILE_PATH = Path(__file__)
FEATURES_DIR = FILE_PATH.parent.parent / "features"
FEATURE_FILE: Path = FEATURES_DIR / "karpenter_test_workflow_with_airflow_api.feature"

# DAG parameters are venue specific
DAG_ID = "karpenter_test"
DAG_PARAMETERS = {"placeholder": 1}


@scenario(FEATURE_FILE, "Execute the Karpenter Test Workflow with the Airflow API")
def test_execute_karpenter_test_workflow_with_the_airflow_api():
    pass


@given("the Airflow API is up and running")
def api_up_and_running():
    pass


@when("I trigger a run for the Karpenter Test DAG using the Airflow API", target_fixture="response")
def trigger_dag(airflow_api_url, fetch_token):

    headers = {"Authorization": f"Bearer {fetch_token}", "Content-Type": "application/json"}
    job_config = {"conf": DAG_PARAMETERS}

    response = requests.post(
        f"{airflow_api_url}/dags/{DAG_ID}/dagRuns",
        headers=headers,
        json=job_config,
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


@then("I see an eventual successful DAG run")
@backoff.on_exception(
    backoff.constant,
    (AssertionError, requests.exceptions.HTTPError),
    max_time=7200,
    giveup=check_failed,
    jitter=None,
    interval=5,
)
def poll_dag_run(response, airflow_api_url, fetch_token):

    headers = {"Authorization": f"Bearer {fetch_token}"}

    if response is not None:
        dag_json = response.json()
        dag_run_response = requests.get(
            f"""{airflow_api_url}/dags/{DAG_ID}/dagRuns/{dag_json["dag_run_id"]}""",
            headers=headers,
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
