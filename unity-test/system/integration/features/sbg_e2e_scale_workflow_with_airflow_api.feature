Feature: SBG End-To-End Scale Workflow with the Airflow API

  As an SBG user
  I want to execute the SBG End-To-End Scale (Preprocess + Isofit) workflow using the Airflow API
  And verify that it completes successfully
  So that I can get data from it

  Scenario: Successful execution of the SBG End-To-End Scale Workflow with the Airflow API
    Given the Airflow API is up and running
    When I trigger a dag run for the SBG End-To-End Scale dag
    Then I receive a response with status code 200
    And I see an eventual successful dag run
