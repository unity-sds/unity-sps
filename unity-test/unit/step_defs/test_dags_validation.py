from pathlib import Path

from airflow.utils.dag_cycle_tester import check_cycle
from pytest_bdd import given, scenarios, then

FILE_PATH = Path(__file__)
FEATURES_DIR = FILE_PATH.parent.parent / "features"
FEATURE_FILE = FEATURES_DIR / "dags_validation.feature"

scenarios(FEATURE_FILE)


@given("the DAGs are loaded")
def the_dags_are_loaded(dagbag):
    return dagbag


@then("no import errors should exist")
def no_import_errors(dagbag):
    assert len(dagbag.import_errors) == 0, f"DAG import failures. Errors: {dagbag.import_errors}"


@then("each task should have a valid owner")
def each_task_should_have_valid_owner(dagbag):
    for dag_id, dag in dagbag.dags.items():
        for task in dag.tasks:
            assert task.owner != "airflow", f"Task {task.task_id} in DAG {dag_id} does not have a valid owner"


@then("each DAG should have correct tags")
def each_dag_should_have_correct_tags(dagbag):
    for dag_id, dag in dagbag.dags.items():
        assert hasattr(dag, "tags"), f"DAG {dag_id} has no tags attribute set."
        assert isinstance(dag.tags, list), f"DAG {dag_id}'s tags attribute is not a list."
        assert len(dag.tags) > 0, f"DAG {dag_id} doesn't have any tags."
        for tag in dag.tags:
            assert isinstance(tag, str), f"Tag {tag} in DAG {dag_id} is not a string."


@then("each DAG should have at least one task")
def each_dag_should_have_at_least_one_task(dagbag):
    for dag_id, dag in dagbag.dags.items():
        assert len(dag.tasks) > 0, f"DAG {dag_id} does not have any tasks"


@then("no DAG should have a cycle")
def no_dag_should_have_a_cycle(dagbag):
    for dag_id, dag in dagbag.dags.items():
        check_cycle(dag)
