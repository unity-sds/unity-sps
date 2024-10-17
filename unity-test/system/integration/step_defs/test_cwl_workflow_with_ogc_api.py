# # This test executes the SBG End-To-End Scale CWL workflow using the OGC API.
# # The workflow parameters are contained in a YAML file which is venue-dependent.
# # The CWL DAG must already be deployed in Airflow,
# # and it is invoked via the OGC API.
# # The CWL task is executed via a KubernetesPodOperator on a worker node
# # that is dynamically provisioned by Karpenter.
# from pathlib import Path
#
# import backoff
# import requests
# from pytest_bdd import scenarios, given, when, then, parsers
# import pytest
#
# import os
# import time
#
# from unity_sds_client.unity import Unity
# from unity_sds_client.unity_services import UnityServices
# from unity_sds_client.resources.job_status import JobStatus
# from unity_sds_client.unity import UnityEnvironments
#
# FILE_PATH = Path(__file__)
# FEATURES_DIR = FILE_PATH.parent.parent / "features"
# FEATURE_FILE: Path = FEATURES_DIR / "cwl_workflow_with_ogc_api.feature"
#
# # DAG parameters are venue specific
# DAG_ID = "cwl_dag"
# # dictionary that contains the request data for different CWL workflows.
# # Note: the YAML file is venue-dependent
# JOB_DATA = {
#     "SBG_DATA": {
#       "inputs": {
#         "cwl_workflow": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/L1-to-L2-e2e.scale.cwl",
#         "cwl_args": "https://raw.githubusercontent.com/unity-sds/sbg-workflows/main/L1-to-L2-e2e.dev.scale.yml",
#         "request_memory": "64Gi",
#         "request_cpu": "32",
#         "request_storage": "100Gi",
#         "use_ecr": True
#       },
#       "outputs": {
#         "result": {
#           "transmissionMode": "reference"
#         }
#       }
#     }
# }
#
# scenarios(FEATURE_FILE)
#
# @given(parsers.parse("The OGC API is up and running for {job_data} and {venue}"))
# @given("The OGC API is up and running for <job_data> and <venue>")
# def api_up_and_running(ogc_processes, job_data, venue):
#
#     assert ogc_processes is not None and len(ogc_processes) > 0
#
#
# @when(parsers.parse("I trigger a job with data {job_data} on venue {venue}"))
# @when("I trigger a job with data '<job_data>' on venue '<venue>'",
#       target_fixture="job")
# def trigger_process(job_data, venue, cwl_dag_process):
#
#     print(cwl_dag_process)
#     assert cwl_dag_process is not None
#
#     print(JOB_DATA[job_data])
#     # job = cwl_dag_process.execute(JOB_DATA[job_data])
#     # assert job is not None
#     job = "job"
#     return job
#
# @then("The job starts executing")
# def check_job_started(job):
#     status = job.get_status().status
#     assert status in [JobStatus.ACCEPTED, JobStatus.RUNNING]
#
# def check_failed(e):
#     if isinstance(e, AssertionError):
#         return "failed" in e.args[0]
#     return False
#
#
# @then("I see an eventual successful job")
# @backoff.on_exception(
#     backoff.constant,
#     (AssertionError, requests.exceptions.HTTPError),
#     max_time=3600,
#     giveup=check_failed,
#     jitter=None,
#     interval=5,
# )
# def check_process_execution_and_termination(job):
#
#     status = job.get_status().status
#     while status in [JobStatus.ACCEPTED, JobStatus.RUNNING]:
#         print(f"Job: {job.id} status: {job.get_status().status}")
#         status = job.get_status().status
#
#     print(f"Job: {job.id} status: {job.get_status().status}")
#     assert job.get_status().status == JobStatus.SUCCESSFUL
