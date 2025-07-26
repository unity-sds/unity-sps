Feature: Execute DAG workflows using the Airflow API

      As a UNITY SPS user
      I want to execute a DAG workflow using the Airflow API
      And verify that it completes successfully
      So that I can inspect the results

      Scenario Outline: Successful execution of a DAG workflow with the Airflow API
            Given the Airflow API is up and running
            When I trigger a dag run for the <test_case> workflow using the <test_dag> DAG
            Then I receive a response with status code 200
            And I see an eventual successful dag run

            Examples:
            | test_case      | test_dag         |
            | KARPENTER      | karpenter_test   |
            | EMIT           | cwl_dag          |
            | SBG_PREPROCESS | cwl_dag          |
            | EMIT           | cwl_dag_modular  |
            | SBG_PREPROCESS | cwl_dag_modular  |
