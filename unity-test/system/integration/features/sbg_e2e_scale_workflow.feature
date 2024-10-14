Feature: Airflow SBG End-To-End Scale Workflow

  As an SBG user
  I want to ensure that SBG End-To-End Scale (Preprocess + Isofit) workflow does not fail
  So that I can get data from it

  Scenario: Check SBG End-To-End Scale Workflow
    Given the Airflow API is up and running
    When I trigger a dag run for the SBG End-To-End Scale dag
    Then I receive a response with status code 200
    And I see an eventual successful dag run
