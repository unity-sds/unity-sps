# unity-sps Testing

## Introduction

This document provides an overview of the testing architecture for the Unity Project. It encompasses continuous testing concepts such as testing across the software development lifecycle as well as automated execution of tests through automation.

---

## Testing Categories

The below list of test categories are included in our testing setup. Further details are provided below.

- [X] **Static Code Analysis:** checks code for syntax, style, vulnerabilities, and bugs
- [X] **Unit Tests:** tests functions or components to verify that they perform as intended
- [X] **Security Tests:** identifies potential security vulnerabilities
- [ ] **Build Tests:** checks if the code builds into binaries or packages successfully
- [ ] **Acceptance Tests:** validates against end-user & stakeholder requirements
- [X] **Integration Tests:** ensure software components interact correctly
- [X] **System Tests:** intended to test the overall software application in an integrated form

### Static Code Analysis

#### Python Code Analysis

- Location: `/.pre-commit-config.yaml`
- Purpose: Perform static code analysis on Python files in the project.
- Running Tests:
  - Manually:
    1. Install `Flake8` by running `pip install flake8`.
    2. Navigate to the project directory and run `flake8 .` to analyze all Python files.
    3. View the results in the terminal.
  - Automatically:
    - Frequency:
      - Triggered by code commits to the `main` branch.
      - Run nightly on all active branches.
    - Results Location: N/A
- Contributing:
  - Framework Used: `Flake8`
  - Tips:
    - Ensure your code follows PEP 8 style guidelines.

#### Markdown Code Analysis

- Location: `/.pre-commit-config.yaml`
- Purpose: Lint markdown files for syntax errors.
- Running Tests:
  - Manually: N/A
  - Automatically:
    - Frequency:
      - Triggered by code commits to the `main` branch.
      - Run nightly on all active branches.
    - Results Location: N/A
- Contributing:
  - Framework Used: `markdownlint-cli`
  - Tips: N/A

#### Python Import Sorting

- Location: `/.pre-commit-config.yaml`
- Purpose: Sort Python imports.
- Running Tests:
  - Manually: N/A
  - Automatically:
    - Frequency:
      - Triggered by code commits to the `main` branch.
      - Run nightly on all active branches.
    - Results Location: N/A
- Contributing:
  - Framework Used: `isort`
  - Tips: N/A

#### Python Code Formatting

- Location: `/.pre-commit-config.yaml`
- Purpose: Format Python code using the Black formatter.
- Running Tests:
  - Manually: N/A
  - Automatically:
    - Frequency:
      - Triggered by code commits to the `main` branch.
      - Run nightly on all active branches.
    - Results Location: N/A
- Contributing:
  - Framework Used: `black`
  - Tips: N/A

#### Ruby Code Analysis

- Location: `/.pre-commit-config.yaml`
- Purpose: Lint Ruby files for syntax errors.
- Running Tests:
  - Manually: N/A
  - Automatically:
    - Frequency:
      - Triggered by code commits to the `main` branch.
      - Run nightly on all active branches.
    - Results Location: N/A
- Contributing:
  - Framework Used: `ruff`
  - Tips: N/A

#### Python Code Security Analysis

- Location: `/.pre-commit-config.yaml`
- Purpose: Check Python code for security vulnerabilities.
- Running Tests:
  - Manually: N/A
  - Automatically:
    - Frequency:
      - Triggered by code commits to the `main` branch.
      - Run nightly on all active branches.
    - Results Location: N/A
- Contributing:
  - Framework Used: `bandit`
  - Tips: N/A

#### Dockerfile Linting

- Location: `/.pre-commit-config.yaml`
- Purpose: Lint Dockerfiles for syntax errors.
- Running Tests:
  - Manually: N/A
  - Automatically:
    - Frequency:
      - Triggered by code commits to the `main` branch.
      - Run nightly on all active branches.
    - Results Location: N/A
- Contributing:
  - Framework Used: `hadolint`
  - Tips: N/A

#### Terraform Configuration Analysis

- Location: `/.pre-commit-config.yaml`
- Purpose: Validate, format, and lint Terraform configuration files.
- Running Tests:
  - Manually: N/A
  - Automatically:
    - Frequency:
      - Triggered by code commits to the `main` branch.
      - Run nightly on all active branches.
    - Results Location: N/A
- Contributing:
  - Framework Used: `pre

### Unit Tests

#### DagBag fixture

- Location: `/unity-test/unit/conftest.py`
- Purpose: Provides a `DagBag` object for testing DAGs.
- Running Tests:
  - Manually: N/A
  - Automatically:
    - Frequency: N/A
    - Results Location: N/A
- Contributing:
  - Framework Used: pytest
  - Tips:
    - This fixture can be used in other test functions to get access to the loaded DAGs.

#### test_dags_validation.py

- Location: `/unity-test/unit/step_defs/test_dags_validation.py`
- Purpose: Tests the DAG validation features using pytest-bdd.
- Running Tests:
  - Manually:
    1. Install the required Python packages: `pip install pytest pytest-bdd apache-airflow`
    2. Run the tests: `pytest test_dags_validation.py`
    3. View the test results in the console output.
  - Automatically:
    - Frequency: On code changes
    - Results Location: N/A
- Contributing:
  - Framework Used: pytest-bdd
  - Tips:
    - The test functions use the `given` and `then` decorators from pytest-bdd to define the test scenarios.
    - Each scenario is defined in the `/unity-test/unit/features/dags_validation.feature` file.
    - The `the_dags_are_loaded` fixture is used to provide the `DagBag` object to the test functions.
    - The test functions assert various properties of the loaded DAGs, such as the absence of import errors, the validity of task owners, the presence of tags, and the absence of DAG cycles.

### Security Tests

- Location: `/unity`
- Purpose: Identify potential security vulnerabilities.
- Running Tests:
  - Manually: N/A
  - Automatically:
    - Frequency:
      - Triggered by code commits to the `main` branch.
      - Run weekly, every Monday at 2:00 AM UTC.
    - Results Location: N/A
- Contributing:
  - Framework Used: `OWASP ZAP` for web application vulnerabilities, `Synk` for dependency checks
  - Tips:
    - Use `Bandit` for Python code static analysis.
    - Follow the [OWASP Top 10 Vulnerabilities](https://owasp.org/www-project-top-ten/).

### Integration Tests

#### airflow_sbg_e2e

- Location: `/unity-test/system/integration`
- Purpose: To ensure that SBG E2E processing does not fail and data can be retrieved from it.
- Running Tests:
  - Manually:
    1. Ensure the Airflow API is up and running.
    2. Trigger a dag run for the SBG E2E dag.
    3. Check the response status code is 200.
    4. Poll the dag run until a successful state is reached.
  - Automatically:
    - Trigger: Code changes.
    - Timing: Nightly.
    - Results Location: `[INSERT PATH OR LOCATION WHERE RESULTS WILL RESIDE]`
- Contributing:
  - Framework Used: pytest-bdd.
  - Tips:
    - Ensure that the Airflow API is up and running before running the tests.
    - Check that the response status code is 200.
    - Poll the dag run until a successful state is reached.

### System Tests

#### Airflow

- Location: `/unity-test/system/smoke`
- Purpose: Ensure that the Airflow API is up and running and each Airflow component is reported as healthy.
- Running Tests:
  - Manually:
    1. Navigate to `/unity-test/system/smoke` folder.
    2. Run `pytest`.
    3. View test results in the terminal.
  - Automatically:
    - Trigger: Code changes.
    - Timing: On every push to the main branch.
    - Results Location: Test results will be displayed in the CI/CD pipeline logs.
- Contributing:
  - Framework Used: `pytest` and `pytest-bdd`
  - Tips:
    - Ensure that all Airflow components are included in the `airflow_components` list.
    - Ensure that the `airflow_api_url` fixture is properly set up.
