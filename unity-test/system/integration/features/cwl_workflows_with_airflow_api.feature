Feature: Execute CWL workflows using the Airflow API

      As a UNITY SPS user
      I want to execute a CWL workflow using the Airflow API
      And verify that it completes successfully
      So that I can inspect the results

      Scenario Outline: Successful execution of a CWL workflow with the Airflow API
            Given the Airflow API is up and running
            When I trigger a dag run for the <test_case> workflow
            Then I receive a response with status code 200
            And I see an eventual successful dag run

            Examples:
            | test_case      |
            | sbg_preprocess |
            | emit           |
            | sbg_e2e_scale  |
