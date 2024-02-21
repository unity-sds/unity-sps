import os

import pytest
from airflow.models import DagBag


@pytest.fixture
def dagbag(mocker):
    mocker.patch("airflow.models.Variable.get", return_value='{"key": "value"}')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dag_folder = os.path.join(script_dir, "../../airflow/dags/")
    return DagBag(
        dag_folder=dag_folder,
        include_examples=False,
    )
