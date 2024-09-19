import os

import boto3
import pytest
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

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


@pytest.fixture(scope="session")
def airflow_api_auth():
    return HTTPBasicAuth("admin", os.getenv("AIRFLOW_WEBSERVER_PASSWORD"))


@pytest.fixture(scope="session")
def session():
    session = boto3.Session(profile_name="mcp-venue-dev")
    return session


@pytest.fixture(scope="session")
def eks_cluster_name(resource_name_template):
    name = resource_name_template.replace("{}", "")
    name = name.replace("--", "-")
    return name
