Feature: EMIT Workflow with the OGC API

  As an EMIT user
  I want to execute the EMIT workflow using the OGC API
  And verify that it completes successfully
  So that I can get data from it

  Scenario: Successful execution of the EMIT Workflow with the OGC API
    Given the OGC API is up and running
    When I trigger a job for the EMIT process
    Then The job starts executing
    And I see an eventual successful job
