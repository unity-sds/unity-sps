from datetime import datetime, timezone
from pathlib import Path

import requests
from pytest_bdd import given, scenario, then, when

FILE_PATH = Path(__file__)
FEATURES_DIR = FILE_PATH.parent.parent / "features"
FEATURE_FILE = FEATURES_DIR / "airflow_api_health.feature"

airflow_components = ["metadatabase", "scheduler", "triggerer", "dag_processor"]


@scenario(FEATURE_FILE, "Check API health")
def test_check_api_health():
    pass


@given("the Airflow API is up and running")
def api_up_and_running():
    pass


@when("I send a GET request to the health endpoint", target_fixture="response")
def send_get_request(airflow_api_url, fetch_token):

    headers = {"Authorization": f"Bearer {fetch_token}"}
    response = requests.get(f"{airflow_api_url}/health", headers=headers, verify=False)  # nosec B501
    return response


@then("I receive a response with status code 200")
def check_status_code(response):
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"


@then("each Airflow component is reported as healthy")
def check_components_health(response):
    data = response.json()
    for c in airflow_components:
        assert data[c]["status"] == "healthy", f"{c} is not healthy"


@then("each Airflow component's last heartbeat was received less than 30 seconds ago")
def check_last_heartbeat(response):
    data = response.json()
    now = datetime.now(timezone.utc)
    for c in airflow_components:
        if c == "metadatabase":
            continue

        last_heartbeat = datetime.strptime(
            data[c]["latest_{}_heartbeat".format(c)],
            "%Y-%m-%dT%H:%M:%S.%f%z",
        )
        assert (now - last_heartbeat).total_seconds() < 30, f"Last {c} heartbeat was more than 30 seconds ago"
