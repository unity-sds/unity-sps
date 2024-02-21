Feature: Airflow DAG validation
    Ensures all the DAGs are valid and well formed.

Scenario: DAGs are imported correctly
    Given the DAGs are loaded
    Then no import errors should exist

Scenario: Tasks have valid owner
    Given the DAGs are loaded
    Then each task should have a valid owner

Scenario: DAGs have correct tags
    Given the DAGs are loaded
    Then each DAG should have correct tags

Scenario: Each DAG has at least one task
    Given the DAGs are loaded
    Then each DAG should have at least one task

Scenario: DAG integrity is preserved
    Given the DAGs are loaded
    Then no DAG should have a cycle
