# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

--------

# [Unity Release 23.2] - 2023-07-14

## Repositories:
- unity-sps : https://github.com/unity-sds/unity-sps/releases/tag/1.1.0
- unity-sps-prototype: https://github.com/unity-sds/unity-sps-prototype/releases/tag/1.1.0
- unity-sps-api: https://github.com/unity-sds/unity-sps-api/releases/tag/1.1.0
- unity-sps-register_job: https://github.com/unity-sds/unity-sps-register_job/releases/tag/1.1.0
- unity-sps-workflows: https://github.com/unity-sds/unity-sps-workflows/releases/tag/1.1.0
- ades_wpst: https://github.com/unity-sds/ades_wpst/releases/tag/1.1.0

## Epics:

- EPIC #7: `jobs-database`
    - [unity-sps-prototype #185] [Epic]: Implement Jobs Database
        - [https://github.com/unity-sds/unity-sps-prototype/issues/185](https://github.com/unity-sds/unity-sps-prototype/issues/185)
    - [unity-sps-prototype #186] [New Feature]: Send SNS message for job creation task
        - [https://github.com/unity-sds/unity-sps-prototype/issues/186](https://github.com/unity-sds/unity-sps-prototype/issues/186)
    - [unity-sps-prototype #187] [New Feature]: Send SNS message for job completion task
        - [https://github.com/unity-sds/unity-sps-prototype/issues/187](https://github.com/unity-sds/unity-sps-prototype/issues/187)
    - [unity-sps-prototype #188] [New Feature]: Consume SNS message for job creation task and job completion tasks
        - [https://github.com/unity-sds/unity-sps-prototype/issues/188](https://github.com/unity-sds/unity-sps-prototype/issues/188)
    - [unity-sps-prototype #189] [New Feature]: Deploy jobs database
        - [https://github.com/unity-sds/unity-sps-prototype/issues/189](https://github.com/unity-sds/unity-sps-prototype/issues/189)
    - [unity-sps-prototype #193) [New Feature]: Create SNS topic, SQS queue and Lambda function for Jobs Database as part of U-SPS deployment
        - [https://github.com/unity-sds/unity-sps-prototype/issues/193](https://github.com/unity-sds/unity-sps-prototype/issues/193)
    - [unity-sps-prototype $194] [Bug]: Prevent duplicate documents in jobs database
        - [https://github.com/unity-sds/unity-sps-prototype/issues/194](https://github.com/unity-sds/unity-sps-prototype/issues/194)   
- EPIC #10: `chirp-workflow-execution`
    - [unity-sps-workflows #8] [Dependency]: Stub implementation for CHIRP workflow
      - [https://github.com/unity-sds/unity-sps-workflows/issues/8](https://github.com/unity-sds/unity-sps-workflows/issues/8)
    - [unity-sps-workflows #12] [Dependency]: Docker container for CMR search
        - [https://github.com/unity-sds/unity-sps-workflows/issues/12](https://github.com/unity-sds/unity-sps-workflows/issues/12)
    - [unity-sps-workflows #14] [Risk]: Processing large data volumes with CWL and Docker
        - [https://github.com/unity-sds/unity-sps-workflows/issues/14](https://github.com/unity-sds/unity-sps-workflows/issues/14)
    -  [unity-sps-prototype #192] [New Feature]: Add an optional PVC to an SPS deployment
       -  [https://github.com/unity-sds/unity-sps-prototype/issues/192](https://github.com/unity-sds/unity-sps-prototype/issues/192)
-  EPIC #1: `min/max scaling`
   - [unity-sps-prototype #141] As a project Manager, i want to set maximum and minimum limits on scaling for processing at venue creation time (static)
     - [https://github.com/unity-sds/unity-sps-prototype/issues/141](https://github.com/unity-sds/unity-sps-prototype/issues/141)
  - EPIC #4: `no magic`
    - [unity-sps-prototype #132] As a user, i want to be explicit about inputs into my process execution (no magic)!
      - [https://github.com/unity-sds/unity-sps-prototype/issues/132](https://github.com/unity-sds/unity-sps-prototype/issues/132)
     
## Docker Containers
- ghcr.io/unity-sds/unity-sps-prototype/hysds-core:unity-v1.1.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-ui-remote:unity-v1.1.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-mozart:unity-v1.1.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-grq2:unity-v1.1.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-verdi:unity-v1.1.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-factotum:unity-v1.1.0
- ghcr.io/unity-sds/unity-sps-prototype/ades-wpst-api:unity-v1.1.0
- ghcr.io/unity-sds/unity-sps-prototype/sps-api-fork:unity-v1.1.0
- ghcr.io/unity-sds/unity-sps-prototype/sps-hysds-pge-base:unity-v1.1.0
- docker.elastic.co/logstash/logstash:7.10.2
- rabbitmq:3.11.13-management
- redis:7.0.10
- docker:23.0.3-dind
- busybox:1.36.0

## Documentation
- Tutorial on using the WPS-T API to register an application package and to execute a job
  - https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/tutorial-execution-of-the-l1b-cwl-workflow-via-the-wps-t-api
- SPS API with examples
  - https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/users-guide/unity-sps-api
- Tutorial on pre-warming a U-SPS cluster
  - https://unity-sds.gitbook.io/docs/~/changes/TMwRbPjXYqq9MCfmRi31/developer-docs/science-processing/docs/developers-guide/manual-verification-testing-the-sps-prewarm-api

## Deployments
- MCP Test:
  - Processing Endpoint (WPS-T API): **http://a720fb4de892844bf884f037c17bb583-1070798053.us-west-2.elb.amazonaws.com:5001**
  - Scaling Endpoint (SPS API): **http://a7096fc6842e84da688b45586d194498-2116025617.us-west-2.elb.amazonaws.com:5002**
- MCP Dev:
  - Processing Endpoint (WPS-T API): **http://aa17aedf4454a4cc596a67a1efb73411-1350404365.us-west-2.elb.amazonaws.com:5001**
  - Scaling Endpoint (SPS API): **http://a440158f49fab4278bdcf2bcb145082b-625745.us-west-2.elb.amazonaws.com:5002**
    
--------
# [Unity Release 23.1] - 2023-04-11

## Repositories:
- unity-sps : https://github.com/unity-sds/unity-sps/releases/tag/1.0.0
- unity-sps-prototype: https://github.com/unity-sds/unity-sps-prototype/releases/tag/1.0.0
- unity-sps-api: https://github.com/unity-sds/unity-sps-api/releases/tag/1.0.0
- unity-sps-register_job: 
  - MCP-Dev: https://github.com/unity-sds/unity-sps-register_job/releases/tag/1.0.0-MCP_Dev
  - MCP-Test: https://github.com/unity-sds/unity-sps-register_job/releases/tag/1.0.0-MCP_Test
- unity-sps-workflows: https://github.com/unity-sds/unity-sps-workflows/releases/tag/1.0.0
- ades_wpst: https://github.com/unity-sds/ades_wpst/releases/tag/1.0.0

## Epics:
- EPIC #130: `ancillary data`
    - [unity-sps-prototype #148] Mount EFS partitions on U-SPS cluster
      - https://github.com/unity-sds/unity-sps-prototype/issues/148
- EPIC #146: `automatic testing`
    - [unity-sps-prototype #153] Smoke test to deploy a simple process and execute a job request
      - https://github.com/unity-sds/unity-sps-prototype/issues/153
- EPIC #132: `no magic`
    - [unity-sps #154]: Pass explicit input parameters to a WPS-T job request
      - https://github.com/unity-sds/unity-sps-prototype/issues/154
    - [unity-sps-prototype #159]: Return the input parameters as part of the WPS-T DescribeProcess method
      - https://github.com/unity-sds/unity-sps-prototype/issues/159
    - [unity-sps-prototype #167]: The WPS-T method to register a process may time out while building the PGE Docker image 
      - https://github.com/unity-sds/unity-sps-prototype/issues/167
- EPIC #142: `processing-instance-types`
    - [unity-sps-prototype #142]: As a project manager, i want to set default compute types for processing nodes at deploy time, so that i can predict costs for the system (Static)
      - https://github.com/unity-sds/unity-sps-prototype/issues/154
- EPIC #162: `u-sps-api`
    - [unity-sps-prototype #163]: New SPS API with stub pre-warm method
      - https://github.com/unity-sds/unity-sps-prototype/issues/163
    - [unity-sps-prototype #167]: Refactor the HySDS workers as a Kubernetes DaemonSet
      - https://github.com/unity-sds/unity-sps-prototype/issues/170
    - [unity-sps-prototype #167]: Scale the number of worker nodes in the Kubernetes cluster
      - https://github.com/unity-sds/unity-sps-prototype/issues/171
    
## Docker Containers
- ghcr.io/unity-sds/unity-sps-prototype/hysds-core:unity-v1.0.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-ui-remote:unity-v1.0.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-mozart:unity-v1.0.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-grq2:unity-v1.0.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-verdi:unity-v1.0.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-factotum:unity-v1.0.0
- ghcr.io/unity-sds/unity-sps-prototype/ades-wpst-api:unity-v1.0.0
- ghcr.io/unity-sds/unity-sps-prototype/sps-api-fork:unity-v1.0.0
- ghcr.io/unity-sds/unity-sps-prototype/sps-hysds-pge-base:unity-v1.0.0
- docker.elastic.co/logstash/logstash:7.10.2
- rabbitmq:3.11.13-management
- redis:7.0.10
- docker:23.0.3-dind
- busybox:1.36.0

## Documentation
- Tutorial on using the WPS-T API to register an application package and to execute a job
  - https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/tutorial-execution-of-the-l1b-cwl-workflow-via-the-wps-t-api
- SPS API with examples
  - https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/users-guide/unity-sps-api
- Tutorial on pre-warming a U-SPS cluster
  - https://unity-sds.gitbook.io/docs/~/changes/TMwRbPjXYqq9MCfmRi31/developer-docs/science-processing/docs/developers-guide/manual-verification-testing-the-sps-prewarm-api

## Deployments
- MCP Test:
  - Processing Endpoint (WPS-T API): http://a720fb4de892844bf884f037c17bb583-1070798053.us-west-2.elb.amazonaws.com:5001
  - Scaling Endpoint (SPS API): http://a7096fc6842e84da688b45586d194498-2116025617.us-west-2.elb.amazonaws.com:5002
- MCP Dev:
  - Processing Endpoint (WPS-T API): http://aa17aedf4454a4cc596a67a1efb73411-1350404365.us-west-2.elb.amazonaws.com:5001
  - Scaling Endpoint (SPS API): http://a440158f49fab4278bdcf2bcb145082b-625745.us-west-2.elb.amazonaws.com:5002
  
------------
