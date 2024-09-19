# Unity SPS Cluster Provisioning with Terraform

## Development Workflow

### Dev Requirements

- [Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli)
- [tfenv](https://github.com/tfutils/tfenv) - Terraform version manager.
- [Pre-commit](https://pre-commit.com/) - Framework for managing and maintaining multi-language pre-commit hooks.
- [act](https://github.com/nektos/act) - Run Github Actions locally.
- [tflint](https://github.com/terraform-linters/tflint) - Terraform Linter.
- [terrascan](https://github.com/accurics/terrascan) - Static code analyzer for Infrastructure as Code.
- [tfsec](https://github.com/aquasecurity/tfsec) - Security scanner for Terraform code.
- [terraform-docs](https://github.com/terraform-docs/terraform-docs) - Generate documentation from Terraform modules.
- [Terratest](https://terratest.gruntwork.io) - Go library that provides patterns and helper functions for testing infrastructure, with 1st-class support for Terraform.

### Auto-generate a terraform.tfvars template file

```shell
cd terraform-unity
terraform-docs tfvars hcl . --output-file "terraform.tfvars"
```

```json
<!-- BEGIN_TF_DOCS -->
celeryconfig_filename  = "celeryconfig_remote.py"
counter                = ""
datasets_filename      = "datasets.remote.template.json"
deployment_environment = "mcp"
docker_images = {
  "ades_wpst_api": "ghcr.io/unity-sds/unity-sps-prototype/ades-wpst-api:unity-v0.0.1",
  "busybox": "k8s.gcr.io/busybox",
  "hysds_core": "ghcr.io/unity-sds/unity-sps-prototype/hysds-core:unity-v0.0.1",
  "hysds_factotum": "ghcr.io/unity-sds/unity-sps-prototype/hysds-factotum:unity-v0.0.1",
  "hysds_grq2": "ghcr.io/unity-sds/unity-sps-prototype/hysds-grq2:unity-v0.0.1",
  "hysds_mozart": "ghcr.io/unity-sds/unity-sps-prototype/hysds-mozart:unity-v0.0.1",
  "hysds_ui": "ghcr.io/unity-sds/unity-sps-prototype/hysds-ui-remote:unity-v0.0.1",
  "hysds_verdi": "ghcr.io/unity-sds/unity-sps-prototype/hysds-verdi:unity-v0.0.1",
  "logstash": "docker.elastic.co/logstash/logstash:7.10.2",
  "mc": "minio/mc:RELEASE.2022-03-13T22-34-00Z",
  "minio": "minio/minio:RELEASE.2022-03-17T06-34-49Z",
  "rabbitmq": "rabbitmq:3-management",
  "redis": "redis:latest"
}
kubeconfig_filepath = ""
mozart_es = {
  "volume_claim_template": {
    "storage_class_name": "gp2-sps"
  }
}
namespace = ""
node_port_map = {
  "ades_wpst_api_service": 30011,
  "grq2_es": 30012,
  "grq2_service": 30002,
  "hysds_ui_service": 30009,
  "minio_service_api": 30007,
  "minio_service_interface": 30008,
  "mozart_es": 30013,
  "mozart_service": 30001
}
service_type = "LoadBalancer"
venue        = ""
<!-- END_TF_DOCS -->%
```

## Deploy the Cluster

### Deploying in into Different MCP Venues

### Deploying into Different EKS Clusters

This method will use Terraform to deploy the Kubernetes cluster represented by the `~/.kube/config` file which is referenced in `terraform-unity/main.tf`. Terraform will deploy the resources in the Kubernetes namespace named in `terrafrom/variables.tf` (defaults to `unity-sps`). Additional variables (including secrets) can be set in `terraform.tfvars`, a template is shown below.

From within the Terraform root module directory (`terraform-unity/`), run the following commands to initialize, and apply the Terraform module:

```bash
cd terraform-unity/
terraform init
terraform apply
```

## Teardown the Cluster

From within the Terraform root module directory (terraform-unity/), run the following command to destroy the SPS cluster:

```shell
terraform destroy
```

## Prior to pushing new changes to the repo, please ensure that you done have the following and the checks have passed

1. Run the pre-commit hooks. These hooks will perform static analysis, linting, security checks. The hooks will also reformat the code to conform to the style guide, and produce the auto-generated documentation of the Terraform module.

   ```shell
   # Run all hooks:
   pre-commit run --files terraform-modules/*
   pre-commit run --files terraform-unity/*
   # Run specific hook:
   pre-commit run <hook_id> --files terraform-modules/terraform-unity-sps-hysds-cluster/*.tf
   pre-commit run <hook_id> --files terraform-unity/*.tf
   ```

2. Run the Github Actions locally. These actions include similar checks to the pre-commit hooks, however, the actions not have the ability to perform reformatting or auto-generation of documentation. This step is meant to mimic the Github Actions which run on the remote CI/CD pipeline.

   ```shell
   # Run all actions:
   act
   # Run specific action:
   act -j "<job_name>"
   act -j terraform_validate
   act -j terraform_fmt
   act -j terraform_tflint
   act -j terraform_tfsec
   act -j checkov
   # You may need to authenticate with Docker hub in order to successfully pull some of the associated images.
   act -j terraform_validate -s DOCKER_USERNAME=<insert-username> -s DOCKER_PASSWORD=<insert-password>
   ```

3. Run the Terratest smoke test. At the moment, this represents a **_very_** basic smoke test for our deployment which simply checks the endpoints of the various services.

   ```shell
   cd terraform-test
   go test -v -run TestTerraformUnity -timeout 30m | tee terratest_output.txt
   ```

## Debugging a Terraform Deployment

It is often useful to modify the level of TF_LOG environment variable when debugging
a Terraform deployment. The levels include: `TRACE`, `DEBUG`, `INFO`, `WARN`, and `ERROR`.

An example of setting the `TF_LOG` environment variable to `INFO`:

```bash
export TF_LOG=INFO
```

Additionally, it is also often useful to pipe the output of a Terraform deployment into a log file.

An example of piping the `terraform apply` output into a file named apply_output.txt:

```bash
terraform apply -no-color 2>&1 | tee apply_output.txt
```

## Auto-generated Documentation of the Unity SPS Terraform Root Module

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.8.2 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | 5.50.0 |
| <a name="requirement_helm"></a> [helm](#requirement\_helm) | 2.13.1 |
| <a name="requirement_kubernetes"></a> [kubernetes](#requirement\_kubernetes) | 2.29.0 |
| <a name="requirement_null"></a> [null](#requirement\_null) | 3.2.2 |
| <a name="requirement_time"></a> [time](#requirement\_time) | 0.11.1 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.50.0 |
| <a name="provider_kubernetes"></a> [kubernetes](#provider\_kubernetes) | 2.29.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_unity-sps-airflow"></a> [unity-sps-airflow](#module\_unity-sps-airflow) | ./modules/terraform-unity-sps-airflow | n/a |
| <a name="module_unity-sps-database"></a> [unity-sps-database](#module\_unity-sps-database) | ./modules/terraform-unity-sps-database | n/a |
| <a name="module_unity-sps-efs"></a> [unity-sps-efs](#module\_unity-sps-efs) | ./modules/terraform-unity-sps-efs | n/a |
| <a name="module_unity-sps-initiators"></a> [unity-sps-initiators](#module\_unity-sps-initiators) | ./modules/terraform-unity-sps-initiators | n/a |
| <a name="module_unity-sps-karpenter-node-config"></a> [unity-sps-karpenter-node-config](#module\_unity-sps-karpenter-node-config) | ./modules/terraform-unity-sps-karpenter-node-config | n/a |
| <a name="module_unity-sps-ogc-processes-api"></a> [unity-sps-ogc-processes-api](#module\_unity-sps-ogc-processes-api) | ./modules/terraform-unity-sps-ogc-processes-api | n/a |

## Resources

| Name | Type |
|------|------|
| [kubernetes_namespace.service_area](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/namespace) | resource |
| [aws_eks_cluster.cluster](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/eks_cluster) | data source |
| [aws_eks_cluster_auth.cluster](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/eks_cluster_auth) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_airflow_docker_images"></a> [airflow\_docker\_images](#input\_airflow\_docker\_images) | Docker images for the associated Airflow services. | <pre>object({<br>    airflow = object({<br>      name = string<br>      tag  = string<br>    })<br>  })</pre> | <pre>{<br>  "airflow": {<br>    "name": "ghcr.io/unity-sds/unity-sps/sps-airflow",<br>    "tag": "2.2.0"<br>  }<br>}</pre> | no |
| <a name="input_airflow_webserver_password"></a> [airflow\_webserver\_password](#input\_airflow\_webserver\_password) | The password for the Airflow webserver and UI. | `string` | n/a | yes |
| <a name="input_airflow_webserver_username"></a> [airflow\_webserver\_username](#input\_airflow\_webserver\_username) | The username for the Airflow webserver and UI. | `string` | `"admin"` | no |
| <a name="input_dag_catalog_repo"></a> [dag\_catalog\_repo](#input\_dag\_catalog\_repo) | Git repository that stores the catalog of Airflow DAGs. | <pre>object({<br>    url                 = string<br>    ref                 = string<br>    dags_directory_path = string<br>  })</pre> | <pre>{<br>  "dags_directory_path": "airflow/dags",<br>  "ref": "develop",<br>  "url": "https://github.com/unity-sds/unity-sps.git"<br>}</pre> | no |
| <a name="input_helm_charts"></a> [helm\_charts](#input\_helm\_charts) | Helm charts for the associated services. | <pre>map(object({<br>    repository = string<br>    chart      = string<br>    version    = string<br>  }))</pre> | <pre>{<br>  "airflow": {<br>    "chart": "airflow",<br>    "repository": "https://airflow.apache.org",<br>    "version": "1.13.1"<br>  },<br>  "keda": {<br>    "chart": "keda",<br>    "repository": "https://kedacore.github.io/charts",<br>    "version": "v2.14.2"<br>  }<br>}</pre> | no |
| <a name="input_karpenter_node_classes"></a> [karpenter\_node\_classes](#input\_karpenter\_node\_classes) | Configuration for karpenter\_node\_classes | <pre>map(object({<br>    volume_size = string<br>  }))</pre> | <pre>{<br>  "airflow-kubernetes-pod-operator-high-workload": {<br>    "volume_size": "300Gi"<br>  },<br>  "default": {<br>    "volume_size": "30Gi"<br>  }<br>}</pre> | no |
| <a name="input_karpenter_node_pools"></a> [karpenter\_node\_pools](#input\_karpenter\_node\_pools) | Configuration for Karpenter node pools | <pre>map(object({<br>    requirements : list(object({<br>      key : string<br>      operator : string<br>      values : list(string)<br>    }))<br>    nodeClassRef : string<br>    limits : object({<br>      cpu : string<br>      memory : string<br>    })<br>    disruption : object({<br>      consolidationPolicy : string<br>      consolidateAfter : string<br>    })<br>  }))</pre> | <pre>{<br>  "airflow-celery-workers": {<br>    "disruption": {<br>      "consolidateAfter": "1m",<br>      "consolidationPolicy": "WhenEmpty"<br>    },<br>    "limits": {<br>      "cpu": "80",<br>      "memory": "320Gi"<br>    },<br>    "nodeClassRef": "default",<br>    "requirements": [<br>      {<br>        "key": "karpenter.k8s.aws/instance-family",<br>        "operator": "In",<br>        "values": [<br>          "m7i",<br>          "m6i",<br>          "m5",<br>          "t3",<br>          "c7i",<br>          "c6i",<br>          "c5",<br>          "r7i",<br>          "r6i",<br>          "r5"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-cpu",<br>        "operator": "Gt",<br>        "values": [<br>          "1"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-cpu",<br>        "operator": "Lt",<br>        "values": [<br>          "9"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-memory",<br>        "operator": "Gt",<br>        "values": [<br>          "8191"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-memory",<br>        "operator": "Lt",<br>        "values": [<br>          "32769"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-hypervisor",<br>        "operator": "In",<br>        "values": [<br>          "nitro"<br>        ]<br>      }<br>    ]<br>  },<br>  "airflow-core-components": {<br>    "disruption": {<br>      "consolidateAfter": "1m",<br>      "consolidationPolicy": "WhenEmpty"<br>    },<br>    "limits": {<br>      "cpu": "40",<br>      "memory": "160Gi"<br>    },<br>    "nodeClassRef": "default",<br>    "requirements": [<br>      {<br>        "key": "karpenter.k8s.aws/instance-family",<br>        "operator": "In",<br>        "values": [<br>          "m7i",<br>          "m6i",<br>          "m5",<br>          "t3",<br>          "c7i",<br>          "c6i",<br>          "c5",<br>          "r7i",<br>          "r6i",<br>          "r5"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-cpu",<br>        "operator": "Gt",<br>        "values": [<br>          "1"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-cpu",<br>        "operator": "Lt",<br>        "values": [<br>          "17"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-memory",<br>        "operator": "Gt",<br>        "values": [<br>          "8191"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-memory",<br>        "operator": "Lt",<br>        "values": [<br>          "32769"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-hypervisor",<br>        "operator": "In",<br>        "values": [<br>          "nitro"<br>        ]<br>      }<br>    ]<br>  },<br>  "airflow-kubernetes-pod-operator": {<br>    "disruption": {<br>      "consolidateAfter": "1m",<br>      "consolidationPolicy": "WhenEmpty"<br>    },<br>    "limits": {<br>      "cpu": "100",<br>      "memory": "400Gi"<br>    },<br>    "nodeClassRef": "default",<br>    "requirements": [<br>      {<br>        "key": "karpenter.k8s.aws/instance-family",<br>        "operator": "In",<br>        "values": [<br>          "m7i",<br>          "m6i",<br>          "m5",<br>          "t3",<br>          "c7i",<br>          "c6i",<br>          "c5",<br>          "r7i",<br>          "r6i",<br>          "r5"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-cpu",<br>        "operator": "Gt",<br>        "values": [<br>          "1"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-cpu",<br>        "operator": "Lt",<br>        "values": [<br>          "17"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-memory",<br>        "operator": "Gt",<br>        "values": [<br>          "8191"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-memory",<br>        "operator": "Lt",<br>        "values": [<br>          "32769"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-hypervisor",<br>        "operator": "In",<br>        "values": [<br>          "nitro"<br>        ]<br>      }<br>    ]<br>  },<br>  "airflow-kubernetes-pod-operator-high-workload": {<br>    "disruption": {<br>      "consolidateAfter": "1m",<br>      "consolidationPolicy": "WhenEmpty"<br>    },<br>    "limits": {<br>      "cpu": "528",<br>      "memory": "1056Gi"<br>    },<br>    "nodeClassRef": "airflow-kubernetes-pod-operator-high-workload",<br>    "requirements": [<br>      {<br>        "key": "karpenter.k8s.aws/instance-family",<br>        "operator": "In",<br>        "values": [<br>          "m7i",<br>          "m6i",<br>          "m5",<br>          "t3",<br>          "c7i",<br>          "c6i",<br>          "c5",<br>          "r7i",<br>          "r6i",<br>          "r5"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-cpu",<br>        "operator": "Gt",<br>        "values": [<br>          "1"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-cpu",<br>        "operator": "Lt",<br>        "values": [<br>          "49"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-memory",<br>        "operator": "Gt",<br>        "values": [<br>          "8191"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-memory",<br>        "operator": "Lt",<br>        "values": [<br>          "98305"<br>        ]<br>      },<br>      {<br>        "key": "karpenter.k8s.aws/instance-hypervisor",<br>        "operator": "In",<br>        "values": [<br>          "nitro"<br>        ]<br>      }<br>    ]<br>  }<br>}</pre> | no |
| <a name="input_kubeconfig_filepath"></a> [kubeconfig\_filepath](#input\_kubeconfig\_filepath) | The path to the kubeconfig file for the Kubernetes cluster. | `string` | n/a | yes |
| <a name="input_mcp_ami_owner_id"></a> [mcp\_ami\_owner\_id](#input\_mcp\_ami\_owner\_id) | The owner ID of the MCP AMIs | `string` | `"794625662971"` | no |
| <a name="input_ogc_processes_docker_images"></a> [ogc\_processes\_docker\_images](#input\_ogc\_processes\_docker\_images) | Docker images for the associated OGC Processes API services. | <pre>object({<br>    ogc_processes_api = object({<br>      name = string<br>      tag  = string<br>    })<br>    git_sync = object({<br>      name = string<br>      tag  = string<br>    })<br>    redis = object({<br>      name = string<br>      tag  = string<br>    })<br>  })</pre> | <pre>{<br>  "git_sync": {<br>    "name": "registry.k8s.io/git-sync/git-sync",<br>    "tag": "v4.2.4"<br>  },<br>  "ogc_processes_api": {<br>    "name": "ghcr.io/unity-sds/unity-sps-ogc-processes-api/unity-sps-ogc-processes-api",<br>    "tag": "2.0.0"<br>  },<br>  "redis": {<br>    "name": "redis",<br>    "tag": "7.4.0"<br>  }<br>}</pre> | no |
| <a name="input_project"></a> [project](#input\_project) | The project or mission deploying Unity SPS. | `string` | `"unity"` | no |
| <a name="input_release"></a> [release](#input\_release) | The software release version. | `string` | `"24.3"` | no |
| <a name="input_service_area"></a> [service\_area](#input\_service\_area) | The service area owner of the resources being deployed. | `string` | `"sps"` | no |
| <a name="input_venue"></a> [venue](#input\_venue) | The MCP venue in which the resources will be deployed. | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_resources"></a> [resources](#output\_resources) | SSM parameter IDs for SPS resources. |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
