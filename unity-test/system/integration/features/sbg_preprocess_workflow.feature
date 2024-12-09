Feature: Airflow SBG Preprocess Workflow

  As an SBG user
  I want to ensure that SBG Preprocess workflow does not fail
  So that I can get data from it

  Scenario: Check SBG Preprocess Workflow
    Given the Airflow API is up and running
    When I trigger a dag run for the SBG Preprocess dag
    Then I receive a response with status code 200
    And I see an eventual successful dag run
