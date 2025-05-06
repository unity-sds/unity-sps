import os

import boto3
import pytest
import requests
from dotenv import load_dotenv
from unity_sds_client.unity import Unity, UnityEnvironments
from unity_sds_client.unity_services import UnityServices

# Load environment variables from .env file
load_dotenv()


def pytest_addoption(parser):
    parser.addoption(
        "--project",
        action="store",
        default="unity",
        help="The project or mission deploying the processing system.",
    )
    parser.addoption(
        "--subsystem",
        action="store",
        default="sps",
        help="The service area/subsystem owner of the resources being deployed.",
    )
    parser.addoption(
        "--venue",
        action="store",
        default=None,
        choices=("dev", "test", "ops"),
        help="The venue in which the cluster will be deployed (dev, test, ops).",
    )
    parser.addoption(
        "--developer",
        action="store",
        default=None,
        help="Identifier for the developer or team responsible for the resource. It is used in the naming convention of the resource. If left empty, it will be excluded from the resource name.",
    )
    parser.addoption(
        "--counter",
        action="store",
        default=None,
        help="Identifier used to uniquely distinguish resources. This is used in the naming convention of the resources.",
    )
    parser.addoption(
        "--airflow-endpoint",
        action="store",
        help="Base URL for the Airflow service endpoint",
    )
    parser.addoption(
        "--ogc-processes-endpoint",
        action="store",
        help="Base URL for the OGC Processes API endpoint",
    )


@pytest.fixture(scope="session")
def resource_name_template(request):
    project = request.config.getoption("--project")
    venue = request.config.getoption("--venue")
    subsystem = request.config.getoption("--subsystem")
    developer = request.config.getoption("--developer")
    counter = request.config.getoption("--counter")

    # Compact: filter out None or empty strings
    components = [project, venue, subsystem, developer, "{}", counter]
    compacted_elements = [element for element in components if element]
    return "-".join(compacted_elements)


@pytest.fixture(scope="session")
def airflow_api_url(request):
    url = request.config.getoption("--airflow-endpoint")
    return url


@pytest.fixture(scope="session")
def ogc_processes_api_url(request):
    url = request.config.getoption("--ogc-processes-endpoint")
    return url


@pytest.fixture(scope="session")
def venue(request):
    venue = request.config.getoption("--venue")
    return venue


# @pytest.fixture(scope="session")
# def airflow_api_auth():
#     return HTTPBasicAuth("admin", os.getenv("AIRFLOW_WEBSERVER_PASSWORD"))


@pytest.fixture(scope="function")
def fetch_token():
    username = os.getenv("UNITY_USER")
    password = os.getenv("UNITY_PASSWORD")
    client_id = os.getenv("UNITY_CLIENT_ID")
    region = "us-west-2"
    url = f"https://cognito-idp.{region}.amazonaws.com"
    payload = {
        "AuthParameters": {"USERNAME": f"{username}", "PASSWORD": f"{password}"},
        "AuthFlow": "USER_PASSWORD_AUTH",
        "ClientId": f"{client_id}",
    }
    # Set headers
    headers = {
        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
        "Content-Type": "application/x-amz-json-1.1",
    }
    # POST request
    res = requests.post(url, json=payload, headers=headers).json()
    if "AuthenticationResult" in res:
        access_token = res["AuthenticationResult"]["AccessToken"]
        return access_token


@pytest.fixture(scope="session")
def session():
    session = boto3.Session(profile_name="mcp-venue-dev")
    return session


@pytest.fixture(scope="session")
def eks_cluster_name(resource_name_template):
    name = resource_name_template.replace("{}", "")
    name = name.replace("--", "-")
    return name


@pytest.fixture(scope="session")
def ogc_processes(ogc_processes_api_url):
    """
    Retrieves the OGC processes available from the given endpoint.
    """

    # setup Unity venue
    unity = Unity(UnityEnvironments.DEV)
    unity.set_venue_id("")
    process_service = unity.client(UnityServices.PROCESS_SERVICE)

    # retrieve all OGC processes
    process_service.endpoint = ogc_processes_api_url
    procs = process_service.get_processes()
    for p in procs:
        print(p)
    return procs


@pytest.fixture(scope="session")
def cwl_dag_process(ogc_processes):
    """
    Selects the CWL classic DAG from the list of available OGC processes
    """

    for p in ogc_processes:
        if p.id == "cwl_dag":
            return p
    return None


@pytest.fixture(scope="session")
def cwl_dag_modular_process(ogc_processes):
    """
    Selects the CWL modular DAG from the list of available OGC processes
    """

    for p in ogc_processes:
        if p.id == "cwl_dag_modular":
            return p
    return None
