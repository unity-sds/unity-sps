Feature: Airflow API health check

  As an Airflow user
  I want to ensure that the Airflow API is up and running
  So that I can interact with it

  Scenario: Check API health
    Given the Airflow API is up and running
    When I send a GET request to the health endpoint
    Then I receive a response with status code 200
    And each Airflow component is reported as healthy
    And each Airflow component's last heartbeat was received less than 30 seconds ago
