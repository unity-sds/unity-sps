# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# [Unity Release 25.3] - 2025-06-30

- SPS Version 3.1.0 (new)
- OGC API Version 2.1.0 (unchanged)
- OGC Python Client Version 2.1.0 (unchanged)

## Overview

This release includes several updates to various Science Processing System components, focusing on scalability and testability:
- An optional High-Load configuration has been built up to support increased processing loads; this may be enabled at install-time.
- Test coverage has been greatly expanded to include the Airflow and OGC APIs, as well as the CWL classic and CWL modular DAGs.
- Additionally, the Cognito authentication interaction has been worked into the SPS integration tests, allowing for the tests to properly access the OGC API.
- Some commonly used DAGs are configured to be automatically installed any time the SPS is deployed.
- The SPS Initiators tooling is now included in the general release.

Additionally, there are a number of small adjustments:
- A number of DAGs have included changes involving instance sizing and type.
- The SPS database instance has been updated to a more recent version, and given increased resource allocation.

## Upgrade Guide

- There are no changes in the Terraform variables required for a standard SPS deployment, but the .tfvars files should be
    regenerated to pick up the new default values (like the version of the Airflow Docker image).
    Optionally, before deployment, the administrator may decide to install a more scalable SPS by using this terraform settimng:
  - helm_values_template = "values_high_load.tmpl.yaml"

## Caveat
- This release does not include updating the Python unity-sds OGC client library: https://github.com/unity-sds/unity-monorepo/tree/main/libs/unity-py/unity_sds_client
  which will not work with any new SPS deployment. This upgrade is expected to be included in the next SPS release.

## Repositories

- unity-sps: <https://github.com/unity-sds/unity-sps/releases/tag/3.1.0>
- unity-sps-ogc-processes-api: <https://github.com/unity-sds/unity-sps-ogc-processes-api/releases/tag/2.1.0>
- unity-sps-ogc-processes-api-client-python: <https://github.com/unity-sds/unity-sps-ogc-processes-api-client-python/releases/tag/2.0.1>

## Docker Containers

- ghcr.io/unity-sds/unity-sps/sps-airflow:3.1.0
- ghcr.io/unity-sds/unity-sps/sps-docker-cwl:3.1.0
- ghcr.io/unity-sds/unity-sps-ogc-processes-api/unity-sps-ogc-processes-api:2.1.0

## Documentation

- For Administrators:
  - [SPS Deployment with Terraform](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/sps-deployment-with-terraform)
  - [Interacting with an Existing SPS Deployment](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/interacting-with-an-existing-sps-deployment)
  - [SPS Airflow Custom Docker Image Build Instructions](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/sps-airflow-custom-docker-image-build-instructions)
  - [Creating an SPS Release](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/creating-an-sps-release)
  - [SPS Post Deployment Operations](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/sps-post-deployment-operations)
  - [SPS Deployment with Marketplace](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/sps-deployment-with-marketplace)
- For Developers:
  - [Developer's Guide Best Practices](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide)
  - [OGC Processes API Overview](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/ogc-processes-api-overview)
  - [Tutorial: Fetching Cognito Authentication Tokens](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/tutorial-fetching-cognito-authentication-tokens)
  - [Tutorial: Using the Airflow API with CURL](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/tutorial-using-the-airflow-api-with-curl)
  - [Tutorial: Using the OGC Processes API with CURL](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/tutorial-using-the-ogc-processes-api-with-curl)
  - [Tutorial: Using the OGC processes API with Python](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/tutorial-using-the-ogc-processes-api-with-python)
- For Users:
  - [Tutorial: Register and Execute a CWL Workflow](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/users-guide/tutorial-register-and-execute-a-cwl-workflow)
  - [Tutorial: Large Scale Testing](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/users-guide/tutorial-large-scale-testing)

## Epics

- EPIC: Airflow/Cognito Integration
  - [[New Feature]: Convert all SPS integration tests to use the Cognito token](https://github.com/unity-sds/unity-sps/issues/384)
- EPIC: Deployment Enhancements
  - [[New Feature]: Register DAGs upon SPS deployment](https://github.com/unity-sds/unity-sps/issues/410)
- EPIC: Continue Application Package Standardization
  - [[New Feature]: Enhancements to CWL Modularized DAG](https://github.com/unity-sds/unity-sps/issues/276)
  - [[New Feature]: Modularize the ASIPS workflows](https://github.com/unity-sds/unity-sps/issues/320)
  - [[New Feature]: Increase test coverage for CWL Modular DAG](https://github.com/unity-sds/unity-sps/issues/394)
  - [[Bug]: Determine if the use of XCOM to hold successful features is causing failures when running DAGs](https://github.com/unity-sds/unity-sps/issues/439)
- EPIC: Demonstrate Space Use Case
  - [[New Feature]: Demonstrate scalability of Space Use Case](https://github.com/unity-sds/unity-sps/issues/285)


# [Unity Release 25.2] - 2025-05-13

- SPS Version 3.0.0 (new)
- OGC API Version 2.0.0 (unchanged)
- OGC Python Client Version 2.0.1 (unchanged)

## Overview

This release supports full integration of Cognito authentication with the Unity Science Processing System:
- Users authenticate to the SPS Airflow User Interface using their Unity Cognito credentials.
- After Cognito authentication, the Airflow native authentication is disabled, so that users only have to login once.
- Programmatic clients will need to use Cognito tokens to interact with the Airflow and OGC APIs.
Because of the changes above, this SPS release is NOT compatible with previous releases (user and client authentication will notwork across releases).

It also contains several efficiency and performance improvements to support scalability:
- Using EC2 types with attached SSD storage
- Prioritization of downstream tasks within the same DAG Run, as opposed to starting new Tasks in other DAG Runs
- Support for sharing large amounts of data across Tasks of the same DAG using S3 mount-points
- Usability improvements for the CWL classic DAG and CWL modular DAG
- Support for periodic clean-up of the Airflow database
- Upgrading SPS to use EKS version 1.31

Finally, this SPS release includes a DAG to create an OGC Application Package from a GitHub repository:
the resulting Docker container can be included in a CWL workflow to process a mission or project specific data assets.

## Upgrade Guide
- Users must obtain a Unity Cognito account to authenticate with the SPS Airflow UI, or to interact with the Airflow and OGC APIs.
- There are no changes in the Terraform variables required for an SPS deployment,
  but the .tfvars files should be regenerated to pick up the new default values (like the version of the Airflow Docker image).

## Caveat
- This release does not include updating the Python unity-sds OGC client library: https://github.com/unity-sds/unity-monorepo/tree/main/libs/unity-py/unity_sds_client
  which will not work with any new SPS deployment. This upgrade is expected to be included in the next SPS release.

## Epics

- EPIC: Airflow/Cognito Integration
  - [[New Feature]: Use Cognito authentication for Airflow and OGC APIs](https://github.com/unity-sds/unity-sps/issues/263)
  - [[New Feature]: Remove the Airflow login](https://github.com/unity-sds/unity-sps/issues/404)
  - [[New Feature]: Update the DAG registration script to use Cognito tokens](https://github.com/unity-sds/unity-sps/issues/405)

- EPIC: SPS Infrastructure
  - [[Enhancement]: Upgrade SPS to latest EKS version 1.30](https://github.com/unity-sds/unity-sps/issues/243)
  - [[New Feature]: Usability improvements to CWL DAGs](https://github.com/unity-sds/unity-sps/issues/335)
  - [[Bug]: Investigate why Airflow tasks get stuck](https://github.com/unity-sds/unity-sps/issues/365)
  - [[Enhancement]: Improve scheduling and execution of tasks](https://github.com/unity-sds/unity-sps/issues/388)
  - [[New Feature]: Investigate new features of Airflow 3.0](https://github.com/unity-sds/unity-sps/issues/389)
  - [[Task] Update tests for CWL (classic) DAG to use the latest version of the Data Services container (9.11.1)](https://github.com/unity-sds/unity-sps/issues/396)
  - [[New Feature]: Create DAG to periodically clean up the Airflow database](https://github.com/unity-sds/unity-sps/issues/400)
  - [[New feature]: Use S3 mount-points to share data across tasks in the same DAG](https://github.com/unity-sds/unity-sps/issues/386)

- EPIC: Application Package Generation Enhancements
  - [[New Feature]: Create DAG to execute the Application Package generator](https://github.com/unity-sds/unity-sps/issues/275)

- EPIC: TROPESS Support
  - [[New Feature]: Support stage-in from Unity DS](https://github.com/unity-sds/unity-sps/issues/351)

## Repositories

- unity-sps: <https://github.com/unity-sds/unity-sps/releases/tag/3.0.0>
- unity-sps-ogc-processes-api: <https://github.com/unity-sds/unity-sps-ogc-processes-api/releases/tag/2.0.0>
- unity-sps-ogc-processes-api-client-python: <https://github.com/unity-sds/unity-sps-ogc-processes-api-client-python/releases/tag/2.0.1>

## Docker Containers

- ghcr.io/unity-sds/unity-sps/sps-airflow:3.0.0
- ghcr.io/unity-sds/unity-sps/sps-docker-cwl:3.0.0
- ghcr.io/unity-sds/unity-sps-ogc-processes-api/unity-sps-ogc-processes-api:2.0.0

## Documentation

- For Administrators:
  - [SPS Deployment with Terraform](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/sps-deployment-with-terraform)
  - [Interacting with an Existing SPS Deployment](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/interacting-with-an-existing-sps-deployment)
  - [SPS Airflow Custom Docker Image Build Instructions](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/sps-airflow-custom-docker-image-build-instructions)
  - [SPS Post Deployment Operations](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/sps-post-deployment-operations)
  - [SPS Deployment with Marketplace](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/sps-deployment-with-marketplace)
- For Developers:
  - [OGC Processes API Overview](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/ogc-processes-api-overview)
  - [Tutorial: Using the OGC Processes API with CURL](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/tutorial-using-the-ogc-processes-api-with-curl)
  - [Tutorial: Using the OGC processes API with Python](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/tutorial-using-the-ogc-processes-api-with-python)
- For Users:
  - [Tutorial: Register and Execute a CWL Workflow](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/users-guide/tutorial-register-and-execute-a-cwl-workflow)


# [Unity Release 25.1] - 2025-04-08

- SPS Version 2.6.0 (new)
- OGC API Version 2.0.0 (unchanged)
- OGC Python Client Version 2.0.1 (unchanged)

## Overview

This release contains several performance improvements to increase the scalability of the SPS system, including:
- New EC2 types available when using the CWL DAG or CWL Modular DAG, including EC2 types with attached SSD storage.
- Prioritization of downstream tasks of running DAGs with respect to upstream tasks of queued DAGs.
- Removal access to shared EFS partition
- Using EC2 types with increased CPU and memory for the core EKS node and core Airflow Pods

Also, the Airflow database is backed up every day, and restored when the SPS system is redeployed.

Additionally, this release includes much expanded support for the SRL (Sample Return Lander) use case,
demonstrating triggering and chaining of data procesisng workflows for generation pof EDR and RDR products
and image format conversion.

Finally, all documentation has been revised and updated.

## Caveats
- Unless ports are specifically opened, this SPS installation is only accessible
  through the top-level MDPS proxies. Users will need to login first with their
  Cognito credentials, then with their Airflow credentials. This issue will be fixed
  when the Airflow/Cognito integration is complete.
- For the same reason, unless ports are specifically opened, the Airflow and OGC
  APIs will not be accessible.

## Upgrade Guide

- This release is backward compatible with the previous version: it includes additional functionality and
  performance improvements, but there are no API changes.
- Because some configuration parameters have changed, the .tfvars files used to deploy EKS, Karpenter and Airflow via Terraform
  should be re-generated to pick up the new values.

## Repositories

- unity-sps: <https://github.com/unity-sds/unity-sps/releases/tag/2.6.0>
- unity-sps-ogc-processes-api: <https://github.com/unity-sds/unity-sps-ogc-processes-api/releases/tag/2.0.0>
- unity-sps-ogc-processes-api-client-python: <https://github.com/unity-sds/unity-sps-ogc-processes-api-client-python/releases/tag/2.0.1>

## Epics

- EPIC: SPS Infrastructure
  - [[Enhancement]: Update the Management Console to use the latest SDS version](https://github.com/unity-sds/unity-sps/issues/280)
  - [[Bug]: Fix placement of Pods over Nodes](https://github.com/unity-sds/unity-sps/issues/304)
  - [[Enhancement] Remove access to shared EFS partition in the CWL DAG](https://github.com/unity-sds/unity-sps/issues/318)
  - [[Bug]: Update CPU and memory limits for worker nodes](https://github.com/unity-sds/unity-sps/issues/330)
  - [[New Feature]: Experiment with using EC2 types with attached storage for better performance](https://github.com/unity-sds/unity-sps/issues/339)
  - [[New Feature]: Log the EC2 Instance Id](https://github.com/unity-sds/unity-sps/issues/357)
  - [[New Feature]: Scale up the SPS core resources](https://github.com/unity-sds/unity-sps/issues/358)
  - [[New Feature]: Prioritize downstream tasks](https://github.com/unity-sds/unity-sps/issues/382)
- EPIC: Deployment Enhancements
  - [[New Feature]: Migrate database content during SPS upgrades](https://github.com/unity-sds/unity-sps/issues/253)
- EPIC: Documentation Updates
  - [[Documentation] OGC Documentation Enhancements](https://github.com/unity-sds/unity-sps/issues/274)
  - [[Documentation]: Revise and update the OGC API Jupyter Notebook](https://github.com/unity-sds/unity-sps/issues/294)
  - [[Documentation]: Provide a high level overview of the OGC Processes API](https://github.com/unity-sds/unity-sps/issues/295)
  - [[Documentation]: Revise and update the OGC tutorial using CURL](https://github.com/unity-sds/unity-sps/issues/296)
  - [[Documentation]: SPS overview for developers](https://github.com/unity-sds/unity-sps/issues/297)
- EPIC: Continue Application Package Standardization
  - [[New Feature]: Modularize the EMIT workflow](https://github.com/unity-sds/unity-sps/issues/302)
- EPIC: TROPESS Support
  - [[Enhancement]: Modular DAG Stage Out step too verbose](https://github.com/unity-sds/unity-sps/issues/307)
- EPIC: Demonstrate Space Use Case
  - [[Enhancement]Create SRL Initiator for EDRGen (.dat + .emd)](https://github.com/unity-sds/unity-sps/issues/287)
  - [[New Feature]: Airflow DAG for EDRgen](https://github.com/unity-sds/unity-sps/issues/278)
  - [[New Feature]: Airflow DAG for RDRgen](https://github.com/unity-sds/unity-sps/issues/279)
  - [[New Feature]: Initiators for EDRgen processing](https://github.com/unity-sds/unity-sps/issues/283)
  - [[New Feature]: Initiators for RDRgen processing](https://github.com/unity-sds/unity-sps/issues/284)
  - [[New Feature]: Prototype routing via a DAG](https://github.com/unity-sds/unity-sps/issues/308)
  - [[New Feature]: Investigate router DAG configuration via Airflow Configuration, SSM, S3 file](https://github.com/unity-sds/unity-sps/issues/324)

## Docker Containers

- ghcr.io/unity-sds/unity-sps/sps-airflow:2.6.0
- ghcr.io/unity-sds/unity-sps/sps-docker-cwl:2.6.0
- ghcr.io/unity-sds/unity-sps-ogc-processes-api/unity-sps-ogc-processes-api:2.0.0

## Documentation

- For Administrators:
  - [SPS Deployment with Terraform](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/sps-deployment-with-terraform)
  - [Interacting with an Existing SPS Deployment](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/interacting-with-an-existing-sps-deployment)
  - [SPS Airflow Custom Docker Image Build Instructions](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/sps-airflow-custom-docker-image-build-instructions)
  - [SPS Post Deployment Operations](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/sps-post-deployment-operations)
  - [SPS Deployment with Marketplace](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/sps-deployment-with-marketplace)
- For Developers:
  - [OGC Processes API Overview](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/ogc-processes-api-overview)
  - [Tutorial: Using the OGC Processes API with CURL](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/tutorial-using-the-ogc-processes-api-with-curl)
  - [Tutorial: Using the OGC processes API with Python](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/tutorial-using-the-ogc-processes-api-with-python)
- For Users:
  - [Tutorial: Register and Execute a CWL Workflow](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/users-guide/tutorial-register-and-execute-a-cwl-workflow)

# [Unity Release 24.4] - 2025-01-02

## Tags

- SPS Version 2.4.0 (new)
- OGC API Version 2.0.0 (unchanged)
- OGC Python Client Version 2.0.1 (new)

## Upgrade Guide

- The CWL DAG ("cwl_dag.py") has changed: instead of requesting
  a certain amount of CPU ("request_cpu") and memory ("request_memory)"
  separately, the client need to specify the desired EC2 instance
  ("request_instance_type"). The value needs to be one of those shown
  in the drop-down menu of the User Interface (for example, "r7i.xlarge", "c6i.8xlarge", etc.).
  The client can still specify the desired size of the attached
  disk ("request_storage").

- The SPS User Interface (Airflow) can be accessed via either of the following methods:
  - The top-level URL (for example, "https://www.dev.mdps.mcp.nasa.gov:4443/unity/dev/sps/home"),
    which will require a Cognito login and (temporarily) an additional Airflow login.
  - The mid-level proxy (for example, "http://unity-dev-httpd-alb-1659665968.us-west-2.elb.amazonaws.com:8080/unity/dev/sps/"),
    which requires an Airflow login, and is only accessible within the JPL VPC.

- A new prototype CWL Modular DAG ("cwl_dag_modular.py") is available, which will run the stage-in, process and
  stage-out tasks as separate CWL workflow, but all in the same EC2 node. To use this DAG,
  users will have to rewrite and modularize their existing CWL workflows which were written as a single document.

## Repositories

- unity-sps: <https://github.com/unity-sds/unity-sps/releases/tag/2.4.0>
- unity-sps-ogc-processes-api: <https://github.com/unity-sds/unity-sps-ogc-processes-api/releases/tag/2.0.0>
- unity-sps-ogc-processes-api-client-python: <https://github.com/unity-sds/unity-sps-ogc-processes-api-client-python/releases/tag/2.0.1>

## Epics

Release tickets: https://github.com/orgs/unity-sds/projects/3/views/53

- EPIC: Airflow/WPS-T Integration
  - [[[New Feature]: Publish ogc-api-python-client to PyPi]](https://github.com/unity-sds/unity-sps/issues/225)
- EPIC: `SPS Infrastructure`
  - [[New Feature]: Upgrade SPS library versions](https://github.com/unity-sds/unity-sps/issues/224)
  - [[New Feature]: Enforce SSL access on SPS S3 buckets](https://github.com/unity-sds/unity-sps/issues/231)
  - [[New feature] Enforce SSL on SPS endpoints](https://github.com/unity-sds/unity-sps/issues/237)
  - [[New Feature] Upgrade Apache Airflow to latest version 2.10.3](https://github.com/unity-sds/unity-sps/issues/238)
  - [[New Feature] Add more CWL workflows to integration tests, use both the Airflow and OGC API](https://github.com/unity-sds/unity-sps/issues/235)
- EPIC: Documentation
  - [[Documentation]: Document programmatic submission via OGC API](https://github.com/unity-sds/unity-sps/issues/213)
- EPIC: Airflow/Cognito Integration
  - [[New Feature] Remove the SPS ALBs for Airflow and OGC API](https://github.com/unity-sds/unity-sps/issues/246)
  - [[New Feature] Experiment with removing the Airflow authentication altogether](https://github.com/unity-sds/unity-sps/issues/242)
- EPIC: Demonstrated Scalability
  - [[New feature]: Concurrent Execution of N SBG end-to-end workflows](https://github.com/unity-sds/unity-sps/issues/64)
  - [[New Feature]: Scale up the EMIT workflow](https://github.com/unity-sds/unity-sps/issues/214)
- EPIC: Unity Marketplace
  - [[New Feature]: Airflow Integration into Unity Marketplace](https://github.com/unity-sds/unity-sps/issues/218)
- EPIC: Application Package Standardization
  - [[New Feature]: Stage-In Task](https://github.com/unity-sds/unity-sps/issues/220)
  - [[New Feature]: Modular Process Task](https://github.com/unity-sds/unity-sps/issues/219)
  - [[New Feature]: Modular Stage-Out Task](https://github.com/unity-sds/unity-sps/issues/221)
  - [[Task]: Investigate logging and errors for CWL workflows](https://github.com/unity-sds/unity-sps/issues/230)

## Docker Containers

- ghcr.io/unity-sds/unity-sps/sps-airflow:2.4.0
- ghcr.io/unity-sds/unity-sps/sps-docker-cwl:2.4.0
- ghcr.io/unity-sds/unity-sps-ogc-processes-api/unity-sps-ogc-processes-api:2.0.0

## Documentation

- For Administrators:
  - [SPS Deployment with Terraform](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/admin-guide/sps-deployment-with-terraform)
  - [Interacting with an Existing SPS Deployment](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/admin-guide/interacting-with-an-existing-sps-deployment)
  - [SPS Airflow Custom Docker Image Build Instructions](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/admin-guide/sps-airflow-custom-docker-image-build-instructions)
  - [SPS Post Deployment Operations](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/admin-guide/sps-post-deployment-operations)
- For Developers:
  - [Tutorial: Deploy, Execute, and Undeploy a Process using the OGC API - Processes](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/developers-guide/tutorial-deploy-execute-and-undeploy-a-process-using-the-ogc-api-processes)
- For Users:
  - [Tutorial: Register and Execute a CWL Workflow](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/users-guide/tutorial-register-and-execute-a-cwl-workflow)


# [Unity Release 24.3] - 2024-09-22

## Tags

- SPS Version 2.2.0
- OGC API Version 2.0.0
- OGC Python Client Version 2.0.0

## Repositories

- unity-sps: <https://github.com/unity-sds/unity-sps/releases/tag/2.2.0>
- unity-sps-ogc-processes-api: <https://github.com/unity-sds/unity-sps-ogc-processes-api/releases/tag/2.0.0>
- unity-sps-ogc-processes-api-client-python: <https://github.com/unity-sds/unity-sps-ogc-processes-api-client-python/releases/tag/2.0.0>

## Epics

- EPIC: `Security`
  - [[Bug]: Upgrade EKS 1.27 AMIs](https://github.com/unity-sds/unity-sps/issues/159)
- EPIC: `Scaling`
  - [[New Feature]: Increase ephemeral disk space for Airflow workers](https://github.com/unity-sds/unity-sps/issues/152)
  - [[New Feature]: Enable users to select the EC2 type to execute a workload](https://github.com/unity-sds/unity-sps/issues/153)
  - [[New Feature]: Set the DAG run status to "failed" if the main worker task failed](https://github.com/unity-sds/unity-sps/issues/189)
  - [[New Feature]: Demonstrate use of ECR within an Airflow DAG (https://github.com/unity-sds/unity-sps/issues/186)
- EPIC: `Airflow/WPS-T Integration`
  - [[New Feature]: Create test to deploy, execute and undeploy the CWL DAG](https://github.com/unity-sds/unity-sps/issues/131)
  - [[New Feature]: Enable execution of OGC data processing requests with arbitrary parameter values](https://github.com/unity-sds/unity-sps/issues/129)
- EPIC: `Production Venue Deployments`
  - [[New Feature]: Airflow HTTPD Proxy development and configuration](https://github.com/unity-sds/unity-sps/issues/125)
  - [[New Feature]: Expose SPS health check endpoints](https://github.com/unity-sds/unity-sps/issues/127)
- EPIC: `SPS Infrastructure`
  - [[New Feature]: Update documentation for SPS deployment](https://github.com/unity-sds/unity-sps/issues/116)
  - [[New Feature]: Review the SPS GitBook documentation](https://github.com/unity-sds/unity-sps/issues/118)
  - [[New Feature]: Store SPS Terraform state on S3](https://github.com/unity-sds/unity-sps/issues/132)
  - [[New Feature]: Parametrize the SPS Integration Tests](https://github.com/unity-sds/unity-sps/issues/155)
  - [[New Feature] Upgrade SPS to latest version of Airflow 2.10.0](https://github.com/unity-sds/unity-sps/issues/195)

## Docker Containers

- ghcr.io/unity-sds/unity-sps/sps-airflow:2.2.0
- ghcr.io/unity-sds/unity-sps/sps-docker-cwl:2.2.0
- ghcr.io/unity-sds/unity-sps-ogc-processes-api/unity-sps-ogc-processes-api:2.0.0

## Documentation

- For Administrators:
  - [SPS Deployment with Terraform](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/admin-guide/sps-deployment-with-terraform)
  - [Interacting with an Existing SPS Deployment](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/admin-guide/interacting-with-an-existing-sps-deployment)
  - [SPS Airflow Custom Docker Image Build Instructions](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/admin-guide/sps-airflow-custom-docker-image-build-instructions)
  - [SPS Post Deployment Operations](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/admin-guide/sps-post-deployment-operations)
- For Developers:
  - [Tutorial: Deploy, Execute, and Undeploy a Process using the OGC API - Processes](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/developers-guide/tutorial-deploy-execute-and-undeploy-a-process-using-the-ogc-api-processes)
- For Users:
  - [Tutorial: Register and Execute a CWL Workflow](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/users-guide/tutorial-register-and-execute-a-cwl-workflow)

# [Unity Release 24.2] - 2024-07-01

## Tags

- SPS Version 2.1.0
- OGC API Version 1.0.0
- OGC Python Client Version 1.0.0

## Repositories

- unity-sps: <https://github.com/unity-sds/unity-sps/releases/tag/2.1.0>
- unity-sps-ogc-processes-api: <https://github.com/unity-sds/unity-sps-ogc-processes-api/releases/tag/1.0.0>
- unity-sps-ogc-processes-api-client-python: <https://github.com/unity-sds/unity-sps-ogc-processes-api-client-python/releases/tag/1.0.0>

## Epics

- EPIC: `Airflow/WPS-T Integration`
  - [[New Feature]: Implement the WPS-T methods execute() and status()](https://github.com/unity-sds/unity-sps/issues/61)
  - [[New Feature]: Implement the WPS-T methods register() and unregister()](https://github.com/unity-sds/unity-sps/issues/62)
  - [[New Feature]: Move the DAGs folder to a shared Persistent Volume](https://github.com/unity-sds/unity-sps/issues/63)
- EPIC: `Airflow Scaling Improvements`
  - [[New Feature]: Implement autoscaling of Kubernetes worker nodes](https://github.com/unity-sds/unity-sps/issues/45)
  - [[New Feature]: Nightly test for SBG end-to-end workflow](https://github.com/unity-sds/unity-sps/issues/65)
  - [[Dependency]: PSE to provide analysis of resources needed by each SBG Task](https://github.com/unity-sds/unity-sps/issues/68)
  - [[New Feature] Only use MCP Golden AMIs](https://github.com/unity-sds/unity-sps/issues/75)
  - [[New Feature] Configure multiple pools of Kubernetes nodes](https://github.com/unity-sds/unity-sps/issues/76)
  - [[New Feature] Retrieve venue-dependent parameters from SSM](https://github.com/unity-sds/unity-sps/issues/77)
  - [[New Feature] Store deployment parameters as AIRFLOW variables](https://github.com/unity-sds/unity-sps/issues/85)
  - [[New Feature] Enable Airflow "plugins" folder](https://github.com/unity-sds/unity-sps/issues/96)
  - [[Task] Add TESTING.md file to SPS repo](https://github.com/unity-sds/unity-sps/issues/99)
- EPIC: `SPS Infrastructure`
  - [[New Feature] Store SPS Terraform state on S3](https://github.com/unity-sds/unity-sps/issues/132)
- EPIC: `SPS Security`
  - [[Bug]: Upgrade EKS 1.27 AMIs](https://github.com/unity-sds/unity-sps/issues/159)
  - [[Bug]: Upgrade to EKS 1.29 AMIs](https://github.com/unity-sds/unity-sps/issues/206)

## Docker Containers

- ghcr.io/unity-sds/unity-sps/sps-airflow:2.1.0
- ghcr.io/unity-sds/unity-sps/sps-docker-cwl:2.1.0
- ghcr.io/unity-sds/unity-sps-ogc-processes-api/unity-sps-ogc-processes-api:1.0.0

## Documentation

- [SPS Deployment with Terraform](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/admin-guide/sps-deployment-with-terraform)
- [Interacting with an Existing SPS Deployment](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/admin-guide/interacting-with-an-existing-sps-deployment)
- [SPS Airflow Custom Docker Image Build Instructions](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/admin-guide/sps-airflow-custom-docker-image-build-instructions)
- [Tutorial: Register, Execute, and Unregister a Process using the OGC API - Processes](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/developers-guide/tutorial-register-execute-and-unregister-a-process-using-the-ogc-api-processes)
- [Tutorial: Register and Execute a CWL Workflow](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/users-guide/tutorial-register-and-execute-a-cwl-workflow)

--------

# [Unity Release 24.1] - 2024-04-09

## Tag

Version 2.0.0

## Repositories

- unity-sps: <https://github.com/unity-sds/unity-sps/releases/tag/2.0.0>
- unity-sps-ogc-processes-api: <https://github.com/unity-sds/unity-sps-ogc-processes-api/releases/tag/2.0.0>

## Epics

- EPIC: `Airflow Deployment`
  - [[New Feature]: Deploy EKS to MCP venues with Terraform](https://github.com/unity-sds/unity-sps/issues/28)
  - [[New Feature]: Deploy Airflow to MCP venues with Terraform (no adaptation yet)](https://github.com/unity-sds/unity-sps/issues/29)
  - [[New Feature]: Create a CWL Operator or simply a CWL DAG to execute a CWL workflow](https://github.com/unity-sds/unity-sps/issues/31)
  - [[New Feature]: Using shared disk space for inter-task communication](https://github.com/unity-sds/unity-sps/issues/32)
  - [[New Feature]: Implement autoscaling of Kubernetes pods on a given set of worker nodes](https://github.com/unity-sds/unity-sps/issues/33)
  - [[Task] Migrate the new SPS with Airflow code to unity-sps repository](https://github.com/unity-sds/unity-sps/issues/34)
  - [[New Feature] Allow choosing EC2 types when deploying an EKS cluster](https://github.com/unity-sds/unity-sps/issues/35)
  - [[New Feature]: Allow propagation of permissions to Docker containers](https://github.com/unity-sds/unity-sps/issues/8)
  - [[New feature] Add Terraform parameters to customize the amount of disk available to each Pod](https://github.com/unity-sds/unity-sps/issues/36)
- EPIC: `SBG Venue Deployment`
  - [[New Feature]: Execution of available SBG worflows](https://github.com/unity-sds/unity-sps/issues/38)
  - [[New Feature]: https://github.com/unity-sds/unity-sps/issues/39](https://github.com/unity-sds/unity-sps/issues/39)
  - [[New Feature]: Execution of additional SBG workflows](https://github.com/unity-sds/unity-sps/issues/40)
  - [[New Feature]: Deployment of latest SPS w/Airflow onto sbg venue](https://github.com/unity-sds/unity-sps/issues/41)
  - [[New feature] Decompose SBG End-To-End CWL Workflow](https://github.com/unity-sds/unity-sps/issues/21)
- EPIC: `SPS Infrastructure`
  - [[Task]: Cleanup of AWS resources](https://github.com/unity-sds/unity-sps/issues/42)
  - [[Task]: Reconfigure SDS Automated Tests](https://github.com/unity-sds/unity-sps/issues/43)
  - [[Task]: Update the SPS documentation for administrators](https://github.com/unity-sds/unity-sps/issues/44)

## Docker Containers

- ghcr.io/unity-sds/unity-sps/sps-airflow:2.0.0
- ghcr.io/unity-sds/unity-sps/sps-docker-cwl:2.0.0
- ghcr.io/unity-sds/unity-sps-ogc-processes-api/unity-sps-ogc-processes-api:2.0.0

## Documentation

- [SPS EKS Cluster Provisioning with Terraform](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/admin-guide/sps-eks-cluster-provisioning-with-terraform)
- [SPS Airflow Deployment with Terraform](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/admin-guide/sps-airflow-deployment-with-terraform)
- [SPS Airflow Custom Docker Image Build Instructions](https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/admin-guide/sps-airflow-custom-docker-image-build-instructions)

--------

# [Unity Release 23.3] - 2023-09-29

## Repositories

- unity-sps-prototype: <https://github.com/unity-sds/unity-sps-prototype/releases/tag/1.2.0>
- unity-sps-api: <https://github.com/unity-sds/unity-sps-api/releases/tag/1.2.0>
- unity-sps-register_job: <https://github.com/unity-sds/unity-sps-register_job/releases/tag/1.2.0>
- unity-sps-workflows: <https://github.com/unity-sds/unity-sps-workflows/releases/tag/1.2.0>
- ades_wpst: <https://github.com/unity-sds/ades_wpst/releases/tag/1.2.0>
- unity-sps : <https://github.com/unity-sds/unity-sps/releases/tag/1.2.0>

## Epics

- EPIC: `workflow metadata`
  - [unity-sps-prototype #210] [New Feature]: Store arbitrary labels in the Jobs Database
    - [https://github.com/unity-sds/unity-sps-prototype/issues/210](https://github.com/unity-sds/unity-sps-prototype/issues/210)
  - [unity-sps-prototype #211] [New Feature]: Query the Jobs Metadata by arbitrary labels
    - [https://github.com/unity-sds/unity-sps-prototype/issues/211](https://github.com/unity-sds/unity-sps-prototype/issues/211)
  - [unity-sps-prototype #217] [Risk]: Evaluate scalability of WPS-T API for querying the Jobs Database
    - [https://github.com/unity-sds/unity-sps-prototype/issues/217](https://github.com/unity-sds/unity-sps-prototype/issues/217)
- EPIC: `chirp-workflow-execution`
  - [unity-sps-workflows #8] [Dependency]: Stub implementation for CHIRP workflow
    - [https://github.com/unity-sds/unity-sps-workflows/issues/8](https://github.com/unity-sds/unity-sps-workflows/issues/8)
  - [unity-sps-workflows #10] [Dependency]: Docker container for execution of CHIRP rebinning PGE
    - [https://github.com/unity-sds/unity-sps-workflows/issues/10](https://github.com/unity-sds/unity-sps-workflows/issues/10)
  - [unity-sps-workflows #11] [Dependency]: Full implementation of CHIRP workflow
    - [https://github.com/unity-sds/unity-sps-workflows/issues/11](https://github.com/unity-sds/unity-sps-workflows/issues/11)
  - [unity-sps-workflows #12] [Dependency]: Docker container for CMR search
    - [https://github.com/unity-sds/unity-sps-workflows/issues/12](https://github.com/unity-sds/unity-sps-workflows/issues/12)
  - [unity-sps-workflows #13] [Dependency]: Docker container for Cataloging
    - [https://github.com/unity-sds/unity-sps-workflows/issues/13](https://github.com/unity-sds/unity-sps-workflows/issues/13)
  - [unity-sps-workflows #14] [Risk]: Processing large data volumes with CWL and Docker
    - [https://github.com/unity-sds/unity-sps-workflows/issues/14](https://github.com/unity-sds/unity-sps-workflows/issues/14)
  - [unity-sps-prototype #192 ] [New Feature]: Add an optional PVC to an SPS deployment
    - [https://github.com/unity-sds/unity-sps-prototype/issues/192](https://github.com/unity-sds/unity-sps-prototype/issues/192)
  - [unity-sps-prototype #195] [Dependency]: Docker container for stage-in step
    - [https://github.com/unity-sds/unity-sps-prototype/issues/195](https://github.com/unity-sds/unity-sps-prototype/issues/195)
  - [unity-sps-prototype #227] [New Feature]: Use stage EFS as data temporary location for CHIRP execution
    - [https://github.com/unity-sds/unity-sps-prototype/issues/227](https://github.com/unity-sds/unity-sps-prototype/issues/227)
- EPIC: `no magic`
  - [unity-sps-prototype #132] As a user, i want to be explicit about inputs into my process execution (no magic)!
    - [https://github.com/unity-sds/unity-sps-prototype/issues/132](https://github.com/unity-sds/unity-sps-prototype/issues/132)
  - [unity-sps-prototype #157] [New Feature]: Pass environment variables to a Docker container execution
    - [https://github.com/unity-sds/unity-sps-prototype/issues/157](https://github.com/unity-sds/unity-sps-prototype/issues/157)
- EPIC: `sps-improvements-23.3`
  - [unity-sps-prototype #221] [Dependency]: Tagging U-SPS resources
    - [https://github.com/unity-sds/unity-sps-prototype/issues/221](https://github.com/unity-sds/unity-sps-prototype/issues/221)
  - [unity-sps-prototype #222] [Dependency]: Add SPS API URL to the SSM store
    - [https://github.com/unity-sds/unity-sps-prototype/issues/222](https://github.com/unity-sds/unity-sps-prototype/issues/222)
  - [unity-sps-prototype #230] [Bug]: One SPS deployment can accidentally execute another SPS deployments deployed process containers
    - [https://github.com/unity-sds/unity-sps-prototype/issues/230](https://github.com/unity-sds/unity-sps-prototype/issues/230)
- EPIC: `workflow-label-inputs`
  - [unity-sps-prototype #160] [New Feature]: Pass arbitrary labels when requesting a job execution
    - [https://github.com/unity-sds/unity-sps-prototype/issues/160](https://github.com/unity-sds/unity-sps-prototype/issues/160)
  - [unity-sps-prototype #181] [Risk]: Define how labels should be specified during workflow submission
    - [https://github.com/unity-sds/unity-sps-prototype/issues/181](https://github.com/unity-sds/unity-sps-prototype/issues/181)

## Docker Containers

- ghcr.io/unity-sds/unity-sps-prototype/hysds-core:unity-v1.2.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-ui-remote:unity-v1.2.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-mozart:unity-v1.2.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-grq2:unity-v1.2.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-verdi:unity-v1.2.0
- ghcr.io/unity-sds/unity-sps-prototype/hysds-factotum:unity-v1.2.0
- ghcr.io/unity-sds/unity-sps-prototype/ades-wpst-api:unity-v1.2.0
- ghcr.io/unity-sds/unity-sps-prototype/sps-api:unity-v1.2.0
- ghcr.io/unity-sds/unity-sps-prototype/sps-hysds-pge-base:unity-v1.2.0
- docker.elastic.co/elasticsearch/elasticsearch:7.9.3
- docker.elastic.co/logstash/logstash:7.10.2
- rabbitmq:3.11.13-management
- redis:7.0.10
- docker:23.0.3-dind
- busybox:1.36.0

## Documentation

- Tutorial on using the WPS-T API to register an application package and to execute a job
  - <https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/tutorial-execution-of-the-l1b-cwl-workflow-via-the-wps-t-api>
- SPS API with examples
  - <https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/users-guide/unity-sps-api>
- Tutorial on pre-warming a U-SPS cluster
  - <https://unity-sds.gitbook.io/docs/~/changes/TMwRbPjXYqq9MCfmRi31/developer-docs/science-processing/docs/developers-guide/manual-verification-testing-the-sps-prewarm-api>
- Description of the Jobs Database: architecture and usage
  - <https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/the-jobs-database#how-jobs-are-updated-in-the-database>

## Deployments

--------

# [Unity Release 23.2] - 2023-07-14

## Repositories

- unity-sps : <https://github.com/unity-sds/unity-sps/releases/tag/1.1.0>
- unity-sps-prototype: <https://github.com/unity-sds/unity-sps-prototype/releases/tag/1.1.0>
- unity-sps-api: <https://github.com/unity-sds/unity-sps-api/releases/tag/1.1.0>
- unity-sps-register_job: <https://github.com/unity-sds/unity-sps-register_job/releases/tag/1.1.0>
- unity-sps-workflows: <https://github.com/unity-sds/unity-sps-workflows/releases/tag/1.1.0>
- ades_wpst: <https://github.com/unity-sds/ades_wpst/releases/tag/1.1.0>

## Epics

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
  - [unity-sps-prototype #192] [New Feature]: Add an optional PVC to an SPS deployment
    - [https://github.com/unity-sds/unity-sps-prototype/issues/192](https://github.com/unity-sds/unity-sps-prototype/issues/192)
- EPIC #1: `min/max scaling`
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
  - <https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/tutorial-execution-of-the-l1b-cwl-workflow-via-the-wps-t-api>
- SPS API with examples
  - <https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/users-guide/unity-sps-api>
- Tutorial on pre-warming a U-SPS cluster
  - <https://unity-sds.gitbook.io/docs/~/changes/TMwRbPjXYqq9MCfmRi31/developer-docs/science-processing/docs/developers-guide/manual-verification-testing-the-sps-prewarm-api>

## Deployments

- MCP Test:
  - Processing Endpoint (WPS-T API): **<http://a720fb4de892844bf884f037c17bb583-1070798053.us-west-2.elb.amazonaws.com:5001>**
  - Scaling Endpoint (SPS API): **<http://a7096fc6842e84da688b45586d194498-2116025617.us-west-2.elb.amazonaws.com:5002>**
- MCP Dev:
  - Processing Endpoint (WPS-T API): **<http://aa17aedf4454a4cc596a67a1efb73411-1350404365.us-west-2.elb.amazonaws.com:5001>**
  - Scaling Endpoint (SPS API): **<http://a440158f49fab4278bdcf2bcb145082b-625745.us-west-2.elb.amazonaws.com:5002>**

--------

# [Unity Release 23.1] - 2023-04-11

## Repositories

- unity-sps : <https://github.com/unity-sds/unity-sps/releases/tag/1.0.0>
- unity-sps-prototype: <https://github.com/unity-sds/unity-sps-prototype/releases/tag/1.0.0>
- unity-sps-api: <https://github.com/unity-sds/unity-sps-api/releases/tag/1.0.0>
- unity-sps-register_job:
  - MCP-Dev: <https://github.com/unity-sds/unity-sps-register_job/releases/tag/1.0.0-MCP_Dev>
  - MCP-Test: <https://github.com/unity-sds/unity-sps-register_job/releases/tag/1.0.0-MCP_Test>
- unity-sps-workflows: <https://github.com/unity-sds/unity-sps-workflows/releases/tag/1.0.0>
- ades_wpst: <https://github.com/unity-sds/ades_wpst/releases/tag/1.0.0>

## Epics

- EPIC #130: `ancillary data`
  - [unity-sps-prototype #148] Mount EFS partitions on U-SPS cluster
    - <https://github.com/unity-sds/unity-sps-prototype/issues/148>
- EPIC #146: `automatic testing`
  - [unity-sps-prototype #153] Smoke test to deploy a simple process and execute a job request
    - <https://github.com/unity-sds/unity-sps-prototype/issues/153>
- EPIC #132: `no magic`
  - [unity-sps #154]: Pass explicit input parameters to a WPS-T job request
    - <https://github.com/unity-sds/unity-sps-prototype/issues/154>
  - [unity-sps-prototype #159]: Return the input parameters as part of the WPS-T DescribeProcess method
    - <https://github.com/unity-sds/unity-sps-prototype/issues/159>
  - [unity-sps-prototype #167]: The WPS-T method to register a process may time out while building the PGE Docker image
    - <https://github.com/unity-sds/unity-sps-prototype/issues/167>
- EPIC #142: `processing-instance-types`
  - [unity-sps-prototype #142]: As a project manager, i want to set default compute types for processing nodes at deploy time, so that i can predict costs for the system (Static)
    - <https://github.com/unity-sds/unity-sps-prototype/issues/154>
- EPIC #162: `u-sps-api`
  - [unity-sps-prototype #163]: New SPS API with stub pre-warm method
    - <https://github.com/unity-sds/unity-sps-prototype/issues/163>
  - [unity-sps-prototype #167]: Refactor the HySDS workers as a Kubernetes DaemonSet
    - <https://github.com/unity-sds/unity-sps-prototype/issues/170>
  - [unity-sps-prototype #167]: Scale the number of worker nodes in the Kubernetes cluster
    - <https://github.com/unity-sds/unity-sps-prototype/issues/171>

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
  - <https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/tutorial-execution-of-the-l1b-cwl-workflow-via-the-wps-t-api>
- SPS API with examples
  - <https://app.gitbook.com/o/xZRqGQeQXJ0RP4VMj7Lq/s/UMIRhLdbRQTvMWop8Il9/developer-docs/science-processing/docs/users-guide/unity-sps-api>
- Tutorial on pre-warming a U-SPS cluster
  - <https://unity-sds.gitbook.io/docs/~/changes/TMwRbPjXYqq9MCfmRi31/developer-docs/science-processing/docs/developers-guide/manual-verification-testing-the-sps-prewarm-api>

## Deployments

- MCP Test:
  - Processing Endpoint (WPS-T API): <http://a720fb4de892844bf884f037c17bb583-1070798053.us-west-2.elb.amazonaws.com:5001>
  - Scaling Endpoint (SPS API): <http://a7096fc6842e84da688b45586d194498-2116025617.us-west-2.elb.amazonaws.com:5002>
- MCP Dev:
  - Processing Endpoint (WPS-T API): <http://aa17aedf4454a4cc596a67a1efb73411-1350404365.us-west-2.elb.amazonaws.com:5001>
  - Scaling Endpoint (SPS API): <http://a440158f49fab4278bdcf2bcb145082b-625745.us-west-2.elb.amazonaws.com:5002>

------------
