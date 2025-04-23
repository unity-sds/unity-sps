"""Enable this DAG to clean the Airflow database from records older than 30 days (or run on-demand)."""

from datetime import UTC, datetime, timedelta

from airflow.decorators import dag
from airflow.models.param import Param
from airflow.operators.bash import BashOperator


@dag(
    dag_id="db_cleanup_dag",
    dag_display_name="Database Cleanup DAG",
    # Run this DAG daily at midnight
    schedule_interval="@daily",
    catchup=False,
    is_paused_upon_creation=True,
    description=__doc__,
    doc_md=__doc__,
    render_template_as_native_obj=True,
    max_active_tasks=1,
    start_date=datetime.now(tz=UTC),
    tags=["Airflow", "database", "cleanup"],
    params={
        "clean_before_timestamp": Param(
            default=(datetime.now(tz=UTC) - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S%z"),
            type="string",
            format="date-time",
            description="Delete records older than this timestamp. Default is 30 days ago.",
        ),
    },
)
def db_cleanup_dag():

    _ = BashOperator(
        task_id="db_cleanup_task",
        bash_command="airflow db clean --yes " "--clean-before-timestamp {{ params.clean_before_timestamp }}",
        do_xcom_push=False,
    )


db_cleanup_dag()
