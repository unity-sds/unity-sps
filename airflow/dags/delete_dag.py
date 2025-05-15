"""A DB Cleanup DAG maintained by Astronomer."""

from datetime import UTC, datetime, timedelta

from airflow.decorators import dag
from airflow.models.param import Param
from airflow.operators.bash import BashOperator


@dag(
    dag_id="delete_dag",
    owner="unity-sps",
    schedule_interval=None,
    catchup=False,
    is_paused_upon_creation=False,
    description=__doc__,
    doc_md=__doc__,
    render_template_as_native_obj=True,
    max_active_tasks=1,
    tags=["cleanup"],
    params={
        "clean_before_timestamp": Param(
            default=datetime.now(tz=UTC) - timedelta(days=90),
            type="string",
            format="date-time",
            description="Delete records older than this timestamp. Default is 90 days ago.",
        ),
        "dag_id": Param(type="string"),
    },
)
def delete_dag():

    delete_dag_task = BashOperator(
        task_id="delete_dag_task",
        bash_command="airflow dags delete {{ params.dag_id }} --yes",
        do_xcom_push=False,
    )

    db_clean_task = BashOperator(
        task_id="db_clean_task",
        bash_command="airflow db clean --yes",
        do_xcom_push=False,
    )

    delete_dag_task >> db_clean_task


delete_dag()
