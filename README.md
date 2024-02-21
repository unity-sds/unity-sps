<!-- Header block for project -->
<hr>

<div align="center">

![logo](https://user-images.githubusercontent.com/3129134/163255685-857aa780-880f-4c09-b08c-4b53bf4af54d.png)

<h1 align="center">Unity SDS Processing Service (U-SPS)</h1>

</div>

<pre align="center">The Unity SDS Processing Service facilitates large-scale data processing for scientific workflows.</pre>

<!-- Header block for project -->

![Version](https://img.shields.io/github/v/tag/unity-sds/unity-sps?label=version) ![License](https://img.shields.io/github/license/unity-sds/unity-sps) [![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](code_of_conduct.md) [![SLIM](https://img.shields.io/badge/Best%20Practices%20from-SLIM-blue)](https://nasa-ammos.github.io/slim/)

[Website](https://unity-sds.gitbook.io) | [Docs](https://unity-sds.gitbook.io/docs/developer-docs/science-processing)

This repository contains high level information (such as documentation, change log, etc.) about the U-SPS software stack. The actual U-SPS code is contained within the following set of GitHub repositories:

* [U-SPS Prototype](https://github.com/unity-sds/unity-sps-prototype): Terraform scripts to deploy the U-SPS cluster (either the HySDS or Airflow implementations)
* [U-SPS Workflows](https://github.com/unity-sds/unity-sps-workflows): Examples of CWL workflows that can be executed on a U-SPS cluster
* [U-SPS API](https://github.com/unity-sds/unity-sps-api): The API used to manage a U-SPS cluster
* [U-SPS Register Job](https://github.com/unity-sds/unity-sps-register_job): Implementation of the WPS-T API with respect to the supported U-SPS back-ends

## Features

* Deployment and execution of scientific data processing algorithms via OGC WPS-T API.
* CWL standard for workflow encoding.
* API management for cluster resources.
* Docker-packaged applications interacting within a Kubernetes cluster.
* U-SPS supports HySDS and Apache Airflow implementations.

## Contents

* [Quick Start](#quick-start)
* [Changelog](#changelog)
* [FAQ](#frequently-asked-questions-faq)
* [Contributing Guide](#contributing)
* [License](#license)
* [Support](#support)

## Quick Start

This guide provides a quick way to get started with our project. Please see our [docs](https://unity-sds.gitbook.io/docs/developer-docs/science-processing) for a more comprehensive overview.

### Requirements

* Docker 20.10 or higher
* Kubernetes 1.20 or higher
* Terraform 0.14 or higher

### Setup Instructions

1. Follow the [U-SPS Setup Guide](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/admin-guide/cluster-provisioning-with-terraform).

### Run Instructions

1. Initialize the Terraform scripts.
2. Apply the Terraform configuration.
3. Monitor the U-SPS status on Kubernetes.
4. Check data processing results.

### Usage Examples

* [Tutorial: Executing the L1B workflow](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/tutorial-execution-of-the-l1b-cwl-workflow-via-the-wps-t-api)
* [Tutorial: Using Job Labels](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/job-labels)
* [Tutorial: Testing the SPS Prewarm API](https://unity-sds.gitbook.io/docs/developer-docs/science-processing/docs/developers-guide/manual-verification-testing-the-sps-prewarm-api)

### Build Instructions (if applicable)

N/A

### Test Instructions (if applicable)

N/A

## Changelog

See our [CHANGELOG.md](CHANGELOG.md) for a history of our changes.

Visit our [releases page](https://github.com/unity-sds/unity-sps/releases) for versioned releases.

## Frequently Asked Questions (FAQ)

Questions about our project? Please see our: [FAQ](https://unity-sds.gitbook.io/docs/faq)

## Contributing

Interested in contributing to our project? Please see our: [CONTRIBUTING.md](CONTRIBUTING.md)

## License

See our: [LICENSE](LICENSE)

## Support

Key points of contact are:

* [@Luca Cinquini](https://github.com/LucaCinquini)
* [@Namrata Malarout](https://github.com/NamrataM)
* [@Drew Meyers](https://github.com/drewm-jpl)
* [@Ryan Hunter](https://github.com/ryanhunter-jpl)
