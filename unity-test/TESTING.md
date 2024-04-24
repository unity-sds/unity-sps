# Unity Project Testing Plan  
   
## Introduction  
   
This document provides an overview of the testing architecture for the Unity Project. It encompasses continuous testing concepts such as testing across the software development lifecycle as well as automated execution of tests through automation.  
   
---  
   
## Types of Testing  
   
The below list of tests are included in our testing setup. Further details are provided below.  
   
- [ ] Unit Tests  
- [ ] System Tests  
  - [ ] Integration Tests  
  - [ ] Security Tests  
  - [ ] Performance Tests  
  - [ ] User Interfaces Tests  
   
### Unit Tests  
   
Our unit tests ensure code is tested at a function, method, or sub-module level.  
   
**Location(s):**  
   
- `/unity/tests/unit`  
- `/unity/components/*/tests`  
   
**Testing Frequency:**  
   
- Triggered by code commits to the `main` branch.  
- Run nightly on all active branches.  
   
#### Contributing Unit Tests  
   
To contribute unit tests, we recommend:  
   
- Leveraging the `pytest` framework  
  - [Directions for using pytest](https://docs.pytest.org/en/stable/getting-started.html)  
- Ensuring your unit tests:  
  - Test every non-trivial function or method in your code  
  - Test conditions including malformed arguments and null conditions  
  - Cover expected exceptions and edge cases  
   
### System Tests  
   
Our system tests are intended to test the overall software application in an integrated form.  
   
#### Integration Tests  
   
Our integration tests ensure software components interact correctly.  
   
**Location(s):**  
   
- `/unity/tests/integration`  
- `/unity/components/*/integration`  
   
**Testing Frequency:**  
   
- Triggered after successful unit test completion on the `main` branch.  
- Run after each significant merge to `main`.  
   
##### Contributing Integration Tests  
   
To contribute integration tests, we recommend:  
   
- Leveraging the `TestCafe` framework for end-to-end scenarios  
  - [Directions for using TestCafe](https://devexpress.github.io/testcafe/documentation/getting-started/)  
- Ensuring your integration tests:  
  - Build your software from components to a whole  
  - Test the interaction between software components and external systems  
   
#### Security Tests  
   
Our security tests aim to keep the software secure against threats.  
   
**Security Testing Frameworks(s):**  
   
- `OWASP ZAP` for web application vulnerabilities  
- `Synk` for dependency checks  
   
**Testing Frequency:**  
   
- Triggered by code commits to the `main` branch.  
- Run weekly, every Monday at 2:00 AM UTC.  
   
##### Adhering to Security Best Practices  
   
- Use `Bandit` for Python code static analysis  
  - [Directions for using Bandit](https://bandit.readthedocs.io/en/latest/)  
- Follow the [OWASP Top 10 Vulnerabilities](https://owasp.org/www-project-top-ten/)  
   
#### Performance Tests  
   
To ensure scalability and resource management.  
   
**Location(s):**  
   
- `/unity/tests/performance`  
- `/unity/components/*/performance`  
   
**Testing Frequency:**  
   
- Triggered monthly and upon significant releases.  
- Run monthly, the first Monday of every month at 4:00 AM UTC.  
   
##### Contributing Performance Tests  
   
- Use `Locust` for simulating user behavior  
  - [Directions for using Locust](https://docs.locust.io/en/stable/quickstart.html)  
- Tests should:  
  - Mimic 2X expected user or resource demand  
  - Handle out-of-memory and disk errors, compute capacity loss, and surges in requests  
   
#### User Interface (UI) Tests  
   
For usability and compliance.  
   
**Location(s):**  
   
- `/unity/tests/ui`  
- `/unity/components/*/ui`  
   
**Testing Frequency:**  
   
- Scheduled quarterly and before release candidates.  
- Next scheduled run: [Insert Date]  
   
##### Contributing UI Tests  
   
- Use `Selenium` for automated UI testing  
  - [Directions for using Selenium](https://selenium-python.readthedocs.io
