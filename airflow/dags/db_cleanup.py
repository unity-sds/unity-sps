"""A DB Cleanup DAG maintained by Astronomer."""

import logging
from datetime import UTC, datetime, timedelta
from typing import List, Optional

from airflow.cli.commands.db_command import all_tables
from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.operators.bash import BashOperator
from airflow.utils.db import reflect_tables
from airflow.utils.db_cleanup import _effective_table_names
from airflow.utils.session import NEW_SESSION, provide_session
from sqlalchemy import func
from sqlalchemy.orm import Session

default_args = {"owner": "unity-sps", "start_date": datetime.utcfromtimestamp(0)}


@dag(
    dag_id="astronomer_db_cleanup_dag",
    default_args=default_args,
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
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
        "tables": Param(
            default=[],
            type=["null", "array"],
            examples=all_tables,
            description="List of tables to clean. Default is all tables.",
        ),
        "dry_run": Param(
            default=False,
            type="boolean",
            description="Print the SQL queries that would be run, but do not execute them. Default is False.",
        ),
        "batch_size_days": Param(
            default=7,
            type="integer",
            description="Number of days in each batch for the cleanup. Default is 7 days.",
        ),
    },
)
def astronomer_db_cleanup_dag():

    @provide_session
    def get_oldest_timestamp(
        tables,
        session: Session = NEW_SESSION,
    ) -> Optional[str]:
        oldest_timestamp_list = []
        existing_tables = reflect_tables(tables=None, session=session).tables
        _, effective_config_dict = _effective_table_names(table_names=tables)
        for table_name, table_config in effective_config_dict.items():
            if table_name in existing_tables:
                orm_model = table_config.orm_model
                recency_column = table_config.recency_column
                oldest_execution_date = (
                    session.query(func.min(recency_column)).select_from(orm_model).scalar()
                )
                if oldest_execution_date:
                    oldest_timestamp_list.append(oldest_execution_date.isoformat())
                else:
                    logging.info(f"No data found for {table_name}, skipping...")
            else:
                logging.warning(f"Table {table_name} not found. Skipping.")

        if oldest_timestamp_list:
            return min(oldest_timestamp_list)

    @task
    def get_chunked_timestamps(**context) -> List:
        batches = []
        start_chunk_time = get_oldest_timestamp(context["params"]["tables"])
        if start_chunk_time:
            start_ts = datetime.fromisoformat(start_chunk_time)
            end_ts = datetime.fromisoformat(context["params"]["clean_before_timestamp"])
            batch_size_days = context["params"]["batch_size_days"]

            while start_ts < end_ts:
                batch_end = min(start_ts + timedelta(days=batch_size_days), end_ts)
                batches.append({"BATCH_TS": batch_end.isoformat()})
                start_ts += timedelta(days=batch_size_days)
        return batches

    # The "clean_archive_tables" task drops archived tables created by the previous "clean_db" task, in case that task fails due to an error or timeout.
    db_archive_cleanup = BashOperator(
        task_id="clean_archive_tables",
        bash_command="""\
            airflow db drop-archived \
        {% if params.tables -%}
             --tables {{ params.tables|join(',') }} \
        {% endif -%}
             --yes \
        """,
        do_xcom_push=False,
        trigger_rule="all_done",
    )

    chunked_timestamps = get_chunked_timestamps()

    (
        BashOperator.partial(
            task_id="db_cleanup",
            bash_command="""\
            airflow db clean \
             --clean-before-timestamp $BATCH_TS \
        {% if params.dry_run -%}
             --dry-run \
        {% endif -%}
             --skip-archive \
        {% if params.tables -%}
             --tables '{{ params.tables|join(',') }}' \
        {% endif -%}
             --verbose \
             --yes \
        """,
            append_env=True,
            do_xcom_push=False,
        ).expand(env=chunked_timestamps)
        >> db_archive_cleanup
    )


astronomer_db_cleanup_dag()
