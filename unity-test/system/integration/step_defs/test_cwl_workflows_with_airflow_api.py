# This test executes the specified CWL workflow
# using the CWL DAG (classic or modular) submitted through the Airflow API.
# The workflow parameters are contained in a YAML file which is venue-dependent.
# The CWL DAGs (classic and modular) must already be deployed in Airflow,
# and it is invoked via the Airflow API.
# The CWL task is executed via a KubernetesPodOperator on a worker node
# that is dynamically provisioned by Karpenter.
import json
from pathlib import Path

import backoff
import requests
from pytest_bdd import given, parsers, scenario, then, when

FILE_PATH = Path(__file__)
FEATURES_DIR = FILE_PATH.parent.parent / "features"
FEATURE_FILE: Path = FEATURES_DIR / "cwl_workflows_with_airflow_api.feature"

# DAG parameters are venue specific
CWL_DAG_ID = "cwl_dag"
CWL_DAG_MODULAR_ID = "cwl_dag_modular"
DAG_PARAMETERS = {
    CWL_DAG_MODULAR_ID: {
        "EMIT": {
            "stac_json": "https://raw.githubusercontent.com/unity-sds/unity-tutorial-application/refs/heads/main/test/stage_in/stage_in_results.json",
            "process_workflow": "https://raw.githubusercontent.com/mike-gangl/unity-OGC-example-application/refs/heads/main/process.cwl",
            "process_args": json.dumps({"example_argument_empty": ""}),
            "log_level": "INFO",
            "request_instance_type": "t3.medium",
            "request_storage": "10Gi",
        },
        "SBG_PREPROCESS": {
            "stac_json": "https://raw.githubusercontent.com/brianlee731/SBG-unity-preprocess-mod/refs/heads/main/test/stage-in/featureCollection.json",
            "process_workflow": "http://awslbdockstorestack-lb-1429770210.us-west-2.elb.amazonaws.com:9998/api/ga4gh/trs/v2/tools/%23workflow%2Fdockstore.org%2Fedwinsarkissian%2FSBG-unity-preprocess-mod/versions/4/PLAIN-CWL/descriptor/%2Fprocess.cwl",
            "process_args": json.dumps({}),
            "log_level": "INFO",
            "request_instance_type": "t3.2xlarge",
            "request_storage": "100Gi",
        },
        "SBG_ISOFIT": {
            "stac_json": "https://raw.githubusercontent.com/brianlee731/SBG-unity-isofit-mod_test/refs/heads/main/test/catalog.json",
            "process_workflow": "http://awslbdockstorestack-lb-1429770210.us-west-2.elb.amazonaws.com:9998/api/ga4gh/trs/v2/tools/%23workflow%2Fdockstore.org%2Fbrianlee731%2FSBG-unity-isofit-mod_test/versions/14/PLAIN-CWL/descriptor/%2Fprocess.cwl",
            "process_args": json.dumps({}),
            "log_level": "INFO",
            "request_instance_type": "r7i.2xlarge",
            "request_storage": "100Gi",
        },
    },
    CWL_DAG_ID: {
        "EMIT": {
            # "cwl_workflow": "http://awslbdockstorestack-lb-1429770210.us-west-2.elb.amazonaws.com:9998/api/ga4gh/trs/v2/tools/%23workflow%2Fdockstore.org%2FGodwinShen%2Femit-ghg/versions/9/plain-CWL/descriptor/workflow.cwl",
            "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/main/emit/GodwinShen/workflow.cwl",
            "cwl_args": {
                # "dev": "https://raw.githubusercontent.com/GodwinShen/emit-ghg/refs/heads/main/test/emit-ghg-dev.json",
                "dev": "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/main/emit/GodwinShen/emit-ghg-dev.json",
                # "test": "https://raw.githubusercontent.com/GodwinShen/emit-ghg/refs/heads/main/test/emit-ghg-test.json",
            },
            "log_level": "INFO",
            "request_storage": "100Gi",
            "request_instance_type": "r7i.2xlarge",
        },
        "SBG_E2E_SCALE": {
            # "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/refs/heads/main/L1-to-L2-e2e.cwl",
            "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/main/sbg/l1-to-l2-e2e/L1-to-L2-e2e.cwl",
            "cwl_args": {
                # "dev": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/refs/heads/main/L1-to-L2-e2e.dev.yml",
                "dev": "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/main/sbg/l1-to-l2-e2e/L1-to-L2-e2e.dev.yml",
            },
            "log_level": "INFO",
            "request_storage": "100Gi",
            # c6i.8xlarge: 32 CPUs, 64 GB memory
            "request_instance_type": "c6i.12xlarge",
        },
        "SBG_PREPROCESS": {
            # "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.cwl",
            "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/main/sbg/preprocess/sbg-preprocess-workflow.cwl",
            "cwl_args": {
                # "dev": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.dev.yml",
                # "test": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess/sbg-preprocess-workflow.test.yml",
                "dev": "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/main/sbg/preprocess/sbg-preprocess-workflow.dev.yml",
                "test": "https://raw.githubusercontent.com/unity-sds/unity-sps-workflows/refs/heads/main/sbg/preprocess/sbg-preprocess-workflow.test.yml",
            },
            "log_level": "INFO",
            "request_storage": "10Gi",
            # c6i.xlarge: 4vCPUs, 8 GB memory
            # r7i.xlarge: 4 CPUs 32 GB memory
            "request_instance_type": "r7i.xlarge",
        },
    },
}


@scenario(FEATURE_FILE, "Successful execution of a CWL workflow with the Airflow API")
def test_successful_execution_of_a_cwl_workflow_with_the_airflow_api():
    pass


@given("the Airflow API is up and running")
def api_up_and_running():
    pass


@when(
    parsers.parse("I trigger a dag run for the {test_case} workflow using the {test_dag} DAG"),
    target_fixture="response",
)
def trigger_dag(airflow_api_url, fetch_token, venue, test_case, test_dag):

    headers = {"Authorization": f"Bearer {fetch_token}", "Content-Type": "application/json"}

    # check that this test_case is enabled for the specified venue and test_dag
    try:

        # configuration common to all DAGs
        job_config = {
            "conf": {
                "log_level": f'{DAG_PARAMETERS[test_dag][test_case]["log_level"]}',
                "request_storage": f'{DAG_PARAMETERS[test_dag][test_case]["request_storage"]}',
                "request_instance_type": f'{DAG_PARAMETERS[test_dag][test_case]["request_instance_type"]}',
            }
        }

        # configuration specific to CWL_DAG
        if test_dag == CWL_DAG_ID:
            job_config["conf"]["cwl_workflow"] = f'{DAG_PARAMETERS[test_dag][test_case]["cwl_workflow"]}'
            job_config["conf"]["cwl_args"] = f'{DAG_PARAMETERS[test_dag][test_case]["cwl_args"][venue]}'

        # configuration specific to CWL_DAG to CWL_DAG_MODULAR_ID
        elif test_dag == CWL_DAG_MODULAR_ID:
            job_config["conf"]["stac_json"] = f'{DAG_PARAMETERS[test_dag][test_case]["stac_json"]}'
            job_config["conf"][
                "process_workflow"
            ] = f'{DAG_PARAMETERS[test_dag][test_case]["process_workflow"]}'
            job_config["conf"]["process_args"] = f'{DAG_PARAMETERS[test_dag][test_case]["process_args"]}'

        response = requests.post(
            f"{airflow_api_url}/dags/{test_dag}/dagRuns",
            # auth=airflow_api_auth,
            headers=headers,
            json=job_config,
            # nosec
            verify=False,
        )
        return response

    except KeyError:
        print(f"Test case: {test_case} is NOT enabled for DAG: {test_dag} in venue: {venue}")
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
            f"""{airflow_api_url}/dags/{dag_json["dag_id"]}/dagRuns/{dag_json["dag_run_id"]}""",
            # auth=airflow_api_auth,
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
