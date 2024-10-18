# This test executes the SBG End-To-End workflow
# using the CWL DAG submitted through the Airflow API.
# The workflow parameters are contained in a YAML file which is venue-dependent.
# The CWL DAG must already be deployed in Airflow,
# and it is invoked via the Airflow API.
# The CWL task is executed via a KubernetesPodOperator on a worker node
# that is dynamically provisioned by Karpenter.
from pathlib import Path

import backoff
import requests
from pytest_bdd import given, scenario, then, when

FILE_PATH = Path(__file__)
FEATURES_DIR = FILE_PATH.parent.parent / "features"
FEATURE_FILE: Path = FEATURES_DIR / "sbg_e2e_scale_workflow_with_airflow_api.feature"

# DAG parameters are venue specific
DAG_ID = "cwl_dag"
DAG_PARAMETERS = {
    "dev": {
        "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main"
                        "/L1-to-L2-e2e.scale.cwl",
        "cwl_args": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main"
                    "/L1-to-L2-e2e.dev.scale.yml",
        "request_memory": "64Gi",
        "request_cpu": "32",
        "request_storage": "100Gi",
        "use_ecr": False
    }
}


@scenario(FEATURE_FILE,
          "Successful execution of the SBG End-To-End Scale Workflow with the Airflow API")
def test_successful_execution_of_sbg_e2e_scale_workflow_with_airflow_api():
    pass


@given("the Airflow API is up and running")
def api_up_and_running():
    pass


@when("I trigger a dag run for the SBG End-To-End Scale dag", target_fixture="response")
def trigger_dag(airflow_api_url, airflow_api_auth, venue):
    # DAG parameters are venue dependent
    cwl_workflow = DAG_PARAMETERS[venue]["cwl_workflow"]
    cwl_args = DAG_PARAMETERS[venue]["cwl_args"]
    request_memory = DAG_PARAMETERS[venue]["request_memory"]
    request_cpu = DAG_PARAMETERS[venue]["request_cpu"]
    request_storage = DAG_PARAMETERS[venue]["request_storage"]
    use_ecr = DAG_PARAMETERS[venue]["use_ecr"]
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
                "use_ecr": use_ecr
             }
        },
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
    interval=5,
)
def poll_dag_run(response, airflow_api_url, airflow_api_auth):
    dag_json = response.json()
    dag_run_response = requests.get(
        f"""{airflow_api_url}/api/v1/dags/{dag_json["dag_id"]}/dagRuns/{dag_json["dag_run_id"]}""",
        auth=airflow_api_auth,
        # nosec
        verify=False,
    )
    assert dag_run_response.status_code == 200, (f"Expected status code 2"
                                                 f"00, but got {response.status_code}")
    json = dag_run_response.json()
    assert "state" in json, 'Expected "state" element in response'
    assert json["state"] == "success"
