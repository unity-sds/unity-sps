""" Code to add additional DAGs folders """

import os

from airflow.models import DagBag

dags_dirs = ["/opt/airflow/system_dags"]

for dir in dags_dirs:
    dag_bag = DagBag(os.path.expanduser(dir), include_examples=False)

    if dag_bag:
        for dag_id, dag in dag_bag.dags.items():
            globals()[dag_id] = dag
