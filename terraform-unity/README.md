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
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.7.2 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | 5.43.0 |
| <a name="requirement_helm"></a> [helm](#requirement\_helm) | 2.12.1 |
| <a name="requirement_kubectl"></a> [kubectl](#requirement\_kubectl) | 2.0.4 |
| <a name="requirement_kubernetes"></a> [kubernetes](#requirement\_kubernetes) | 2.25.2 |
| <a name="requirement_null"></a> [null](#requirement\_null) | 3.2.2 |
| <a name="requirement_random"></a> [random](#requirement\_random) | 3.6.0 |

## Providers

No providers.

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_unity-sps-airflow"></a> [unity-sps-airflow](#module\_unity-sps-airflow) | ./modules/terraform-unity-sps-airflow | n/a |

## Resources

No resources.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_airflow_webserver_password"></a> [airflow\_webserver\_password](#input\_airflow\_webserver\_password) | The password for the Airflow webserver and UI. | `string` | n/a | yes |
| <a name="input_counter"></a> [counter](#input\_counter) | Identifier used to uniquely distinguish resources. This is used in the naming convention of the resource. If left empty, a random hexadecimal value will be generated and used instead. | `string` | `""` | no |
| <a name="input_deployment_name"></a> [deployment\_name](#input\_deployment\_name) | The name of the deployment. | `string` | n/a | yes |
| <a name="input_docker_images"></a> [docker\_images](#input\_docker\_images) | Docker images for the associated services. | <pre>object({<br>    airflow = object({<br>      name = string<br>      tag  = string<br>    }),<br>    ogc_processes_api = object({<br>      name = string<br>      tag  = string<br>    })<br>  })</pre> | <pre>{<br>  "airflow": {<br>    "name": "ghcr.io/unity-sds/unity-sps/sps-airflow",<br>    "tag": "2.0.0"<br>  },<br>  "ogc_processes_api": {<br>    "name": "ghcr.io/unity-sds/unity-sps-ogc-processes-api/unity-sps-ogc-processes-api",<br>    "tag": "2.0.0"<br>  }<br>}</pre> | no |
| <a name="input_helm_charts"></a> [helm\_charts](#input\_helm\_charts) | Helm charts for the associated services. | <pre>map(object({<br>    repository = string<br>    chart      = string<br>    version    = string<br>  }))</pre> | <pre>{<br>  "airflow": {<br>    "chart": "airflow",<br>    "repository": "https://airflow.apache.org",<br>    "version": "1.13.1"<br>  },<br>  "karpenter": {<br>    "chart": "karpenter",<br>    "repository": "oci://public.ecr.aws/karpenter",<br>    "version": "0.36.0"<br>  },<br>  "keda": {<br>    "chart": "keda",<br>    "repository": "https://kedacore.github.io/charts",<br>    "version": "v2.13.2"<br>  }<br>}</pre> | no |
| <a name="input_karpenter_default_node_class_metadata_options"></a> [karpenter\_default\_node\_class\_metadata\_options](#input\_karpenter\_default\_node\_class\_metadata\_options) | Disruption policy for the default Karpenter node pool | <pre>object({<br>    httpEndpoint            = string<br>    httpPutResponseHopLimit = number<br>  })</pre> | <pre>{<br>  "httpEndpoint": "enabled",<br>  "httpPutResponseHopLimit": 3<br>}</pre> | no |
| <a name="input_karpenter_default_node_pool_disruption"></a> [karpenter\_default\_node\_pool\_disruption](#input\_karpenter\_default\_node\_pool\_disruption) | Disruption policy for the default Karpenter node pool | <pre>object({<br>    consolidationPolicy = string<br>    consolidateAfter    = string<br>  })</pre> | <pre>{<br>  "consolidateAfter": "30s",<br>  "consolidationPolicy": "WhenEmpty"<br>}</pre> | no |
| <a name="input_karpenter_default_node_pool_limits"></a> [karpenter\_default\_node\_pool\_limits](#input\_karpenter\_default\_node\_pool\_limits) | Limits for the default Karpenter node pool | <pre>object({<br>    cpu    = number # Total CPU limit across all nodes provisioned by this Provisioner<br>    memory = string # Total memory limit across all nodes<br>  })</pre> | <pre>{<br>  "cpu": 80,<br>  "memory": "320Gi"<br>}</pre> | no |
| <a name="input_karpenter_default_node_pool_requirements"></a> [karpenter\_default\_node\_pool\_requirements](#input\_karpenter\_default\_node\_pool\_requirements) | Requirements for the default Karpenter node pool | <pre>map(object({<br>    key      = string<br>    operator = string<br>    values   = list(string)<br>  }))</pre> | <pre>{<br>  "instance_category": {<br>    "key": "karpenter.k8s.aws/instance-category",<br>    "operator": "In",<br>    "values": [<br>      "m",<br>      "t",<br>      "c",<br>      "r"<br>    ]<br>  },<br>  "instance_cpu": {<br>    "key": "karpenter.k8s.aws/instance-cpu",<br>    "operator": "In",<br>    "values": [<br>      "2",<br>      "4",<br>      "8",<br>      "16",<br>      "32"<br>    ]<br>  },<br>  "instance_generation": {<br>    "key": "karpenter.k8s.aws/instance-generation",<br>    "operator": "Gt",<br>    "values": [<br>      "2"<br>    ]<br>  },<br>  "instance_hypervisor": {<br>    "key": "karpenter.k8s.aws/instance-hypervisor",<br>    "operator": "In",<br>    "values": [<br>      "nitro"<br>    ]<br>  }<br>}</pre> | no |
| <a name="input_kubeconfig_filepath"></a> [kubeconfig\_filepath](#input\_kubeconfig\_filepath) | The path to the kubeconfig file for the Kubernetes cluster. | `string` | n/a | yes |
| <a name="input_mcp_al2_eks_optimized_ami"></a> [mcp\_al2\_eks\_optimized\_ami](#input\_mcp\_al2\_eks\_optimized\_ami) | The MCP Amazon Linux 2 (AL2) EKS Optimized AMI | <pre>object({<br>    image_id = string<br>    owner    = string<br>  })</pre> | <pre>{<br>  "image_id": "ami-0121a9a72d2b29816",<br>  "owner": "794625662971"<br>}</pre> | no |
| <a name="input_project"></a> [project](#input\_project) | The project or mission deploying Unity SPS. | `string` | `"unity"` | no |
| <a name="input_release"></a> [release](#input\_release) | The software release version. | `string` | `"2.0.0"` | no |
| <a name="input_service_area"></a> [service\_area](#input\_service\_area) | The service area owner of the resources being deployed. | `string` | `"sps"` | no |
| <a name="input_venue"></a> [venue](#input\_venue) | The MCP venue in which the resources will be deployed. | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_resources"></a> [resources](#output\_resources) | SSM parameter IDs for pipeline resources. |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
