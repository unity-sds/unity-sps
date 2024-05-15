Feature: OGC Processes API health check

  As an API user
  I want to ensure that the OGC Processes API is up and running
  So that I can interact with it

  Scenario: Check API health
    Given the OGC Processes API is up and running
    When I send a GET request to the health endpoint
    Then I receive a response with status code 200
    And the response body contains a key value pair of 'status':'OK'
