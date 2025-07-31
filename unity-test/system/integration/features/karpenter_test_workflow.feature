Feature: Airflow Karpenter Test Workflow

  As an SPS user
  I want to ensure that the system has been successfully deployed to a given venue
  So that I can execute workflows as DAGs while provisioning nodes as needed

  Scenario: Execute the Karpenter Test Workflow
    Given the Airflow API is up and running
    When I trigger a run for the Karpenter Test DAG
    Then I receive a response with status code 200
    And I see an eventual successful DAG run
