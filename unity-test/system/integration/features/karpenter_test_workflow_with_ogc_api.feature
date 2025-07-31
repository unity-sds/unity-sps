Feature: Karpenter Test Workflow with OGC API

  As an SPS user
  I want to ensure that the system has been successfully deployed to a given venue
  So that I can execute workflows as DAGs while provisioning nodes as needed

  Scenario: Execute the Karpenter Test Workflow with the OGC API
    Given the OGC API is up and running
    When I trigger a run for the Karpenter Test DAG using the OGC API
    Then the job starts executing
    And I see an eventual successful job
