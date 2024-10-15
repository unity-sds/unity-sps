Feature: SBG End-To-End Scale Workflow with the OGC API

  As an SBG user
  I want to execute the SBG End-To-End Scale (Preprocess + Isofit) workflow using the OGC API
  And verify that it completes successfully
  So that I can get data from it

  Scenario: Successful execution of the SBG End-To-End Scale Workflow with the OGC API
    Given the OGC API is up and running
    When I trigger a job for the SBG End-To-End Scale process
    Then The job starts executing
    And I see an eventual successful job
