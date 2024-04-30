Feature: Airflow SBG E2E processing check

  As an SBG user
  I want to ensure that SBG E2E processing does not fail
  So that I can get data from it

  Scenario: Check SBG E2E processing
    Given the Airflow API is up and running
    When I trigger a dag run for the SBG E2E dag
    Then I receive a response with status code 200
    And I see an eventual successful dag run
