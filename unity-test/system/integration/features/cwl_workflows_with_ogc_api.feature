Feature: Execute DAG workflows using the OGC API

      As a UNITY SPS user
      I want to execute a DAG workflow using the OGC API
      And verify that it completes successfully
      So that I can inspect the results

      Scenario Outline: Successful execution of a DAG workflow with the OGC API
            Given the OGC API is up and running
            When I trigger a <test_case> OGC job for the <test_dag> OGC process
            Then the job starts executing
            And I see an eventual successful job

            Examples:
            | test_case      | test_dag         |
            | KARPENTER      | karpenter_test   |
            | EMIT           | cwl_dag          |
            | SBG_PREPROCESS | cwl_dag          |
            | EMIT           | cwl_dag_modular  |
            | SBG_PREPROCESS | cwl_dag_modular  |
