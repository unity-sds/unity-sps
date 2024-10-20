Feature: SBG Preprocess Workflow with the Airflow API

  As an SBG user
  I want to execute the SBG Preprocess workflow using the Airflow API
  And verify that it completes successfully
  So that I can get data from it

  Scenario: Successful execution of the SBG Preprocess Workflow with the Airflow API
    Given The Airflow API is up and running
    When I trigger a dag run for the SBG Preprocess dag
    Then I receive a response with status code 200
    And I see an eventual successful dag run

