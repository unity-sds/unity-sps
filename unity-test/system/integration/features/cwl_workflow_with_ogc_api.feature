#Feature: Testing the CWL Workflow with the OGC API
#  As an SPS user
#  I want to execute a CWL workflow through the OGC API
#  And verify that it completes successfully
#  So that I can get data from it

#  Scenario Outline: Successful execution of a CWL workflow using the OGC API
#      Given The OGC API is up and running for <job_data> and <venue>
#      When I trigger a job with data <job_data> on venue <venue>
#      Then The job starts executing
#      And I see an eventual successful job

#  Examples:
#      | job_data  | venue |
#      | SBG_DATA  | dev   |
