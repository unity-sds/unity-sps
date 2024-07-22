# import json
# import re
# from datetime import datetime, timezone

# import boto3
# import jsonschema
# from airflow import DAG
# from airflow.decorators import task
# from airflow.operators.trigger_dagrun import TriggerDagRunOperator
# import pendulum
# from jinja2 import Template
# from airflow.models.param import Param


# default_args = {"owner": "unity-sps", "start_date": datetime.fromtimestamp(0, tz=timezone.utc)}
# dag = DAG(
#     "srl_example_dag",
#     default_args=default_args,
#     description="An example DAG converted from AWS Lambda",
#     schedule=None,
#     start_date=pendulum.today("UTC").add(days=-1),
#     is_paused_upon_creation=False,
#     tags=["example"],
#     params={"filename": Param("test", type="string")},
# )


# # Helper functions
# def render_template(template, values=dict()):
#     template_str = json.dumps(template)
#     pattern = r'"{{\s*[^}]+?\|\s*tojson\s*}}"'
#     replacement_func = lambda m: m.group(0)[1:-1]
#     template_str = re.sub(pattern, replacement_func, template_str)
#     template_obj = Template(template_str)
#     rendered_template_str = template_obj.render(values)
#     rendered_template = json.loads(rendered_template_str)
#     return rendered_template


# def stage_in_static_json(key):
#     with open(key, "r") as file:
#         content = file.read()
#     json_content = json.loads(content)
#     return json_content


# @task
# def identify_dataset(filename, dp_templates):
#     matched_dp_obj = None
#     matched_dp_name = None
#     matched_dp_template = None
#     for dp_name, dp_template in dp_templates.items():
#         matched_dp_obj = re.fullmatch(dp_template["regex_pattern"], filename)

#         if not matched_dp_obj:
#             continue

#         matched_dp_name = dp_name
#         matched_dp_template = dp_template
#         break

#     if not matched_dp_obj:
#         raise ValueError

#     dp_id = matched_dp_template["data_product_id_format"].format(**matched_dp_obj.groupdict())
#     dp = {"data_product_name": matched_dp_name, "data_product_id": dp_id}
#     print(f"Data product: {dp}")
#     return dp


# @task
# def identify_dags(dp, rc_templates):
#     dags = list()
#     for dag_id, rc in rc_templates.items():
#         if dp["data_product_name"] not in rc["required_input_data_products"]:
#             continue
#         dags.append(dag_id)
#     print(f"Matched DAGS:{dags}")
#     return dags


# @task
# def generate_run_configs(dp, dags, dp_templates, rc_templates):
#     osl_bucket = "your-osl-bucket"  # Replace with actual value
#     isl_bucket = "your-isl-bucket"  # Replace with actual value
#     config_bucket = "your-config-bucket"  # Replace with actual value

#     filtered_rc_templates = {dag_id: rc_templates[dag_id] for dag_id in dags}
#     run_configs = dict()
#     matched_dp_name = dp["data_product_name"]
#     matched_dp_id = dp["data_product_id"]
#     dp_rendered_dict = render_template(
#         dp_templates[matched_dp_name],
#         {"DATA_PRODUCT_ID": matched_dp_id, "ISL_BUCKET": isl_bucket},
#     )
#     for dag_id, rc in filtered_rc_templates.items():
#         rc_values = {matched_dp_name.upper(): dp_rendered_dict}

#         # Perform additional matching for non-direct match required_input_data_products
#         # TODO this needs to be figured out...

#         # Add required static data to required input files and run config
#         for req_static_dp in rc["required_static_data"]:
#             static_dp = dp_templates[req_static_dp]
#             static_dp_rendered_dict = render_template(static_dp, {"CONFIG_BUCKET": config_bucket})
#             rc_values[req_static_dp.upper()] = static_dp_rendered_dict

#         # Add expected output data products to run config
#         for exp_output_dp in rc["expected_output_data_products"]:
#             exp_dp = dp_templates[exp_output_dp]
#             exp_dp_rendered_dict = render_template(exp_dp, {"OSL_BUCKET": osl_bucket})
#             rc_values[exp_output_dp.upper()] = exp_dp_rendered_dict

#         rc_template_rendered = render_template(rc, rc_values)
#         run_configs[dag_id] = rc_template_rendered

#     print(f"Generated Run Configs:{run_configs}")
#     return run_configs


# @task
# def validate_run_configs(run_configs):
#     dp_schema = stage_in_static_json("data_products/data_products.schema.json")
#     rc_schema = stage_in_static_json("run_configs/run_config.schema.json")

#     schemas = {
#         rc_schema["$id"]: rc_schema,
#         dp_schema["$id"]: dp_schema,
#     }
#     resolver = jsonschema.RefResolver.from_schema(rc_schema, store=schemas)
#     rc_schema_validator = jsonschema.Draft202012Validator(rc_schema, resolver=resolver)

#     for _, rc in run_configs.items():
#         rc_schema_validator.validate(rc)

#     print("Validated Run Configs")


# @task
# def evaluate_dag_triggers(run_configs):
#     def file_exists(bucket, key):
#         s3_client = boto3.client("s3")
#         try:
#             s3_client.get_object(
#                 Bucket=bucket,
#                 Key=key,
#             )
#             return True
#         except s3_client.exceptions.NoSuchKey:
#             return False

#     def get_required_files(run_config):
#         required_files = list()

#         for _, dp in run_config["required_input_data_products"].items():
#             required_files.extend(dp["files"])

#         for _, static_data in run_config["required_static_data"].items():
#             required_files.extend(static_data["files"])

#         return required_files

#     filtered_run_configs = dict()
#     for dag_id, rc in run_configs.items():
#         should_trigger_dag = True
#         required_files = get_required_files(rc)
#         missing_files = []

#         for rf in required_files:
#             if not file_exists(rf["bucket"], rf["key"]):
#                 missing_files.append(f'Bucket: {rf["bucket"]}, Key: {rf["key"]}')
#                 should_trigger_dag = False

#         if not should_trigger_dag:
#             missing_files_str = "\n".join(missing_files)
#             print(
#                 f"Not all of the required files exist in S3 to be able to run the following DAG: {dag_id}. Missing files:\n{missing_files_str}"
#             )
#             continue
#         print(f"All of the required files exist in S3 to be able to run the following DAG: {dag_id}")
#         filtered_run_configs[dag_id] = rc

#     print(f"Evaluated DAG Triggers: {filtered_run_configs}")
#     return filtered_run_configs


# with dag:
#     dp_templates = stage_in_static_json("data_products/data_products_templates.jinja2.json")
#     rc_templates = stage_in_static_json("run_configs/run_config_templates.jinja2.json")

#     dp = identify_dataset(filename, dp_templates)
#     dags = identify_dags(dp, rc_templates)
#     run_configs = generate_run_configs(dp, dags, dp_templates, rc_templates)
#     validate_run_configs(run_configs)
#     filtered_run_configs = evaluate_dag_triggers(run_configs)

#     for dag_id, rc in filtered_run_configs.items():
#         trigger_dag = TriggerDagRunOperator(
#             task_id=f"trigger_dag_{dag_id}",
#             trigger_dag_id=dag_id,
#             conf=rc,
#             reset_dag_run=True,
#             wait_for_completion=True,
#             poke_interval=60,
#             allowed_states=["success"],
#             failed_states=["failed", "upstream_failed"],
#             trigger_rule="all_done",
#         )
#         trigger_dag.set_upstream(filtered_run_configs)

"""
# DAG Name: Hello World

# Purpose

# Usage
"""  # noqa: E501

import os
import time
from datetime import datetime

from airflow.operators.python import PythonOperator

from airflow import DAG

default_args = {
    "owner": "unity-sps",
    "start_date": datetime.utcfromtimestamp(0),
}


def hello_world():
    print("Hello World")
    time.sleep(30)


def write_to_shared_data():
    file_path = "/shared-task-data/test_file.txt"  # Adjust the path as necessary
    with open(file_path, "w") as f:
        f.write("This is a test file written at " + str(datetime.now()) + "\n")
    print(f"Successfully written to {file_path}")


def read_from_shared_data():
    file_path = "/shared-task-data/test_file.txt"  # Adjust the path as necessary
    try:
        with open(file_path, "r") as f:
            contents = f.read()
        print(f"File contents:\n{contents}")
    except FileNotFoundError:
        print("File not found. Make sure the file path is correct.")


def delete_shared_data_file():
    file_path = "/shared-task-data/test_file.txt"  # Adjust the path as necessary
    try:
        os.remove(file_path)
        print(f"Successfully deleted {file_path}")
    except FileNotFoundError:
        print("File not found. Make sure the file path is correct.")


with DAG(
    dag_id="eval_srl_edrgen_readiness",
    default_args=default_args,
    schedule=None,
    is_paused_upon_creation=False,
    tags=["test"],
) as dag:
    hello_world_task = PythonOperator(
        task_id="hello_world",
        python_callable=hello_world,
    )

    write_to_shared_data_task = PythonOperator(
        task_id="write_to_shared_data",
        python_callable=write_to_shared_data,
    )

    read_from_shared_data_task = PythonOperator(
        task_id="read_from_shared_data",
        python_callable=read_from_shared_data,
    )

    delete_shared_data_file_task = PythonOperator(
        task_id="delete_shared_data_file",
        python_callable=delete_shared_data_file,
    )

    (
        hello_world_task
        >> write_to_shared_data_task
        >> read_from_shared_data_task
        >> delete_shared_data_file_task
    )
