"""
# DAG Name: EMIT Workflow

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
    dag_id="emit_workflow",
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
