from pathlib import Path

import requests
from pytest_bdd import given, scenario, then, when

FILE_PATH = Path(__file__)
FEATURES_DIR = FILE_PATH.parent.parent / "features"
FEATURE_FILE = FEATURES_DIR / "ogc_processes_api_health.feature"


@scenario(FEATURE_FILE, "Check API health")
def test_check_api_health():
    pass


@given("the OGC Processes API is up and running")
def api_up_and_running():
    pass


@when("I send a GET request to the health endpoint", target_fixture="response")
def send_get_request(ogc_processes_api_url):
    response = requests.get(f"{ogc_processes_api_url}/health", verify=False)
    print(response.json())
    return response


@then("I receive a response with status code 200")
def check_status_code(response):
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"


@then("the response body contains a key value pair of 'status':'OK'")
def check_response_body(response):
    data = response.json()
    assert "status" in data.keys()
    status = data["status"]
    assert status == "OK", f"Expected value of 'OK', but got {status}"
