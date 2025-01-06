import os

from unity_sds_client.unity import Unity, UnityEnvironments
from unity_sds_client.unity_services import UnityServices

DAG_ID = "cwl_dag"

CWL_DAG_PROCESS = {
    "executionUnit": {"image": "ghcr.io/unity-sds/unity-sps/sps-docker-cwl:2.1.0", "type": "docker"},
    "processDescription": {
        "description": "This process executes any CWL workflow.",
        "id": "cwl_dag",
        "inputs": {
            "cwl_args": {
                "description": "The URL of the CWL workflow's YAML parameters file",
                "maxOccurs": 1,
                "minOccurs": 1,
                "schema": {"format": "uri", "type": "string"},
                "title": "CWL Workflow Parameters URL",
            },
            "cwl_workflow": {
                "description": "The URL of the CWL workflow",
                "maxOccurs": 1,
                "minOccurs": 1,
                "schema": {"format": "uri", "type": "string"},
                "title": "CWL Workflow URL",
            },
            "request_cpu": {
                "description": "The number of CPU cores requested for the job",
                "maxOccurs": 1,
                "minOccurs": 1,
                "schema": {"type": "string"},
                "title": "Requested CPU",
            },
            "request_memory": {
                "default": "8Gi",
                "description": "The amount of memory requested for the job",
                "maxOccurs": 1,
                "minOccurs": 1,
                "schema": {"type": "string"},
                "title": "Requested Memory",
            },
            "request_storage": {
                "description": "The amount of storage requested for the job",
                "maxOccurs": 1,
                "minOccurs": 1,
                "schema": {"type": "string"},
                "title": "Requested Storage",
            },
        },
        "jobControlOptions": ["async-execute"],
        "outputs": {
            "result": {
                "description": "The result of the SBG Preprocess Workflow execution",
                "schema": {"$ref": "some-ref"},
                "title": "Process Result",
            }
        },
        "title": "Generic CWL Process",
        "version": "1.0.0",
    },
}


def main():

    # setup Unity venue
    unity = Unity(UnityEnvironments.DEV)
    unity.set_venue_id("")
    process_service = unity.client(UnityServices.PROCESS_SERVICE)

    # read specific OGC API URL from environment
    OGC_API = os.environ.get("OGC_API", None)
    print(f"Using OGC_API URL={OGC_API}")
    process_service.endpoint = OGC_API

    # register process
    print(f"Registering process: {DAG_ID}")
    response = process_service.deploy_process(CWL_DAG_PROCESS)
    print(response)

    # query DAG back
    # retrieve all OGC processes
    processes = process_service.get_processes()

    # select the desired process
    process = None
    for p in processes:
        if p.id == DAG_ID:
            process = p
    print(process)


if __name__ == "__main__":
    main()
