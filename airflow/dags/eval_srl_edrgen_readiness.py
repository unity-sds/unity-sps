import hashlib
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List

import jsonschema
from airflow.decorators import task
from airflow.exceptions import AirflowException
from airflow.models import Variable
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from jinja2 import Template
from referencing import Registry, Resource

from airflow import DAG

# get the airflow.task logger
task_logger = logging.getLogger("airflow.task")

default_args = {
    "owner": "unity-sps",
    "start_date": datetime.utcfromtimestamp(0),
}


def render_template(template, values=dict()):
    template_str = json.dumps(template)
    pattern = r'"{{\s*[^}]+?\|\s*tojson\s*}}"'
    replacement_func = lambda m: m.group(0)[1:-1]
    template_str = re.sub(pattern, replacement_func, template_str)
    template_obj = Template(template_str)
    rendered_template_str = template_obj.render(values)
    rendered_template = json.loads(rendered_template_str)
    return rendered_template


@task
def identify_dataset(dp_templates: Dict, dp_filename: str) -> Dict:
    for dp_name, dp_template in dp_templates.items():
        matched_dp_obj = re.fullmatch(dp_template["regex_pattern"], dp_filename)
        if matched_dp_obj:
            dp_id = dp_template["data_product_id_format"].format(**matched_dp_obj.groupdict())
            return {"data_product_name": dp_name, "data_product_id": dp_id}
    raise ValueError("No matching data product found")


@task
def identify_dags(run_config_templates: Dict, data_product_name: str) -> List[str]:
    return [
        dag_id
        for dag_id, rc in run_config_templates.items()
        if data_product_name in rc["required_input_data_products"]
    ]


@task
def generate_run_configs(
    run_config_templates: Dict, data_product_templates: Dict, dags: List[str], dp: Dict
) -> Dict:
    osl_bucket = Variable.get("osl_bucket")
    isl_bucket = Variable.get("isl_bucket")
    config_bucket = Variable.get("config_bucket")

    run_configs = {}
    matched_dp_name = dp["data_product_name"]
    matched_dp_id = dp["data_product_id"]
    dp_rendered_dict = render_template(
        data_product_templates[matched_dp_name],
        {"DATA_PRODUCT_ID": matched_dp_id, "ISL_BUCKET": isl_bucket},
    )

    for dag_id in dags:
        rc = run_config_templates[dag_id]
        rc_values = {matched_dp_name.upper(): dp_rendered_dict}

        for req_static_dp in rc["required_static_data"]:
            static_dp = data_product_templates[req_static_dp]
            static_dp_rendered_dict = render_template(static_dp, {"CONFIG_BUCKET": config_bucket})
            rc_values[req_static_dp.upper()] = static_dp_rendered_dict

        for exp_output_dp in rc["expected_output_data_products"]:
            exp_dp = data_product_templates[exp_output_dp]
            exp_dp_rendered_dict = render_template(exp_dp, {"OSL_BUCKET": osl_bucket})
            rc_values[exp_output_dp.upper()] = exp_dp_rendered_dict

        run_configs[dag_id] = render_template(rc, rc_values)

    return run_configs


@task
def validate_run_configs(run_configs: Dict) -> Dict:
    dp_schema = json.loads(Variable.get("dp_schema"))
    rc_schema = json.loads(Variable.get("rc_schema"))

    registry = Registry().with_resources(
        [
            ("dp_schema.json", Resource.from_contents(dp_schema)),
            ("rc_schema.json", Resource.from_contents(rc_schema)),
        ]
    )

    rc_schema_validator = jsonschema.Draft202012Validator(rc_schema, registry=registry)

    for _, rc in run_configs.items():
        rc_schema_validator.validate(rc)

    return run_configs


@task(multiple_outputs=True)
def evaluate_dag_triggers(run_configs: Dict) -> Dict:
    s3_hook = S3Hook()

    def file_exists(bucket: str, key: str) -> bool:
        return s3_hook.check_for_key(key, bucket_name=bucket)

    def get_required_files(run_config: Dict) -> List[Dict]:
        required_files = []
        for dp in run_config["required_input_data_products"].values():
            required_files.extend(dp["files"])
        for static_data in run_config["required_static_data"].values():
            required_files.extend(static_data["files"])
        return required_files

    filtered_run_configs = {}
    for dag_id, rc in run_configs.items():
        required_files = get_required_files(rc)
        missing_files = [
            f'Bucket: {rf["bucket"]}, Key: {rf["key"]}'
            for rf in required_files
            if not file_exists(rf["bucket"], rf["key"])
        ]

        if missing_files:
            task_logger.warning(
                f"Not all required files exist for DAG: {dag_id}. Missing files:\n" + "\n".join(missing_files)
            )
        else:
            task_logger.info(f"All required files exist for DAG: {dag_id}")
            filtered_run_configs[dag_id] = rc

    return filtered_run_configs


@task
def read_json_file(filename: str) -> Dict:
    """
    Read a JSON file from the include directory.

    :param filename: Name of the JSON file to read
    :return: Parsed JSON content as a dictionary
    """
    dag_folder = os.path.dirname(__file__)
    file_path = os.path.join(dag_folder, "..", "include", filename)
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        raise AirflowException(f"File not found: {file_path}")
    except json.JSONDecodeError:
        raise AirflowException(f"Invalid JSON in file: {file_path}")


with DAG(
    dag_id="eval_srl_edrgen_readiness",
    default_args=default_args,
    schedule=None,
    catchup=False,
    tags=["srl", "edr"],
    doc_md="""
    This DAG evaluates SRL EDR generation readiness by checking for the existence of required files
    and triggering downstream DAGs if all prerequisites are met.
    """,
) as dag:
    filename = "{{ dag_run.conf['filename'] }}"
    bucket = "{{ dag_run.conf['bucket'] }}"

    dp_templates = read_json_file("dp_templates.json")
    rc_templates = read_json_file("rc_templates.json")

    dp = identify_dataset(dp_templates, filename)
    dags = identify_dags(rc_templates, dp["data_product_name"])
    run_configs = generate_run_configs(rc_templates, dp_templates, dags, dp)
    validated_run_configs = validate_run_configs(run_configs)
    filtered_run_configs = evaluate_dag_triggers(validated_run_configs)

    for dag_id, rc in filtered_run_configs.items():
        required_files = [file["key"] for file in rc["required_input_data_products"]["STACAM_RawDP"]["files"]]
        filename_string = "".join(required_files)
        dag_run_id = hashlib.sha256(filename_string.encode()).hexdigest()

        trigger_dag = TriggerDagRunOperator(
            task_id=f"trigger_dag_{dag_id}",
            trigger_dag_id=dag_id,
            conf={"run_config": rc},
            execution_date="{{ execution_date }}",
            reset_dag_run=True,
            wait_for_completion=True,
            poke_interval=60,
            allowed_states=["success"],
            failed_states=["failed", "upstream_failed"],
            dag_run_id=dag_run_id,
        )
        (
            dp_templates
            >> rc_templates
            >> dp
            >> dags
            >> run_configs
            >> validated_run_configs
            >> filtered_run_configs
            >> trigger_dag
        )
