Feature: EMIT Workflow with the Airflow API

  As an EMIT user
  I want to execute the EMIT workflow using the Airflow API
  And verify that it completes successfully
  So that I can get data from it

  Scenario: Successful execution of the EMIT Workflow with the Airflow API
    Given the Airflow API is up and running
    When I trigger a dag run for the EMIT workflow
    Then I receive a response with status code 200
    And I see an eventual successful dag run
