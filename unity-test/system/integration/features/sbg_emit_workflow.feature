Feature: Airflow EMIT Workflow

  As an EMIT user
  I want to ensure that the EMIT workflow does not fail
  So that I can get data from it

  Scenario: Check EMIT Workflow
    Given the Airflow API is up and running
    When I trigger a dag run for the EMIT dag
    Then I receive a response with status code 200
    And I see an eventual successful dag run
