import os
import time

from unity_sds_client.resources.job_status import JobStatus
from unity_sds_client.unity import Unity, UnityEnvironments
from unity_sds_client.unity_services import UnityServices

DAG_ID = "cwl_dag"

JOB_PARAMS_SBG_E2E = {
    "inputs": {
        "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main"
        "/L1-to-L2-e2e.scale.cwl",
        "cwl_args": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main"
        "/L1-to-L2-e2e.dev.scale.yml",
        "request_memory": "64Gi",
        "request_cpu": "32",
        "request_storage": "100Gi",
        "use_ecr": True,
    },
    "outputs": {"result": {"transmissionMode": "reference"}},
}

# JOB_PARAMS_SBG_PREPROCESS = {
#         "inputs": {
#             "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main"
#             "/preprocess/sbg-preprocess-workflow.cwl",
#             "cwl_args": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/preprocess"
#                         "/sbg-preprocess-workflow.dev.yml",
#             # r7i.xlarge (4 CPU, 32 GiB memory)
#             "request_memory": "4Gi",
#             "request_cpu": "2",
#             "request_storage": "10Gi",
#             "use_ecr": False,
#         },
#         "outputs": {"result": {"transmissionMode": "reference"}},
# }


def main():

    # setup Unity venue
    unity = Unity(UnityEnvironments.DEV)
    unity.set_venue_id("")
    process_service = unity.client(UnityServices.PROCESS_SERVICE)

    # read specific OGC API URL from environment
    OGC_API = os.environ.get("OGC_API", None)
    print(f"Using OGC_API URL={OGC_API}")
    process_service.endpoint = OGC_API

    # retrieve all OGC processes
    processes = process_service.get_processes()

    # select the desired process
    process = None
    for p in processes:
        if p.id == DAG_ID:
            process = p
    print(process)

    # submit OGC job
    job = process.execute(JOB_PARAMS_SBG_E2E)

    # monitor job until completion (success or error)
    status = job.get_status().status
    while status in [JobStatus.ACCEPTED, JobStatus.RUNNING]:
        print(f"Job: {job.id} status: {job.get_status().status}")
        status = job.get_status().status
        time.sleep(5)
    print(f"Job: {job.id} status: {job.get_status().status}")


if __name__ == "__main__":
    main()
