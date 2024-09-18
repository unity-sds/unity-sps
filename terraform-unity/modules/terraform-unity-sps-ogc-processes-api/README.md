<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.8.2 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | 5.67.0 |
| <a name="requirement_kubernetes"></a> [kubernetes](#requirement\_kubernetes) | 2.32.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.67.0 |
| <a name="provider_kubernetes"></a> [kubernetes](#provider\_kubernetes) | 2.32.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_lambda_invocation.unity_proxy_lambda_invocation](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/lambda_invocation) | resource |
| [aws_ssm_parameter.ogc_processes_api_health_check_endpoint](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.ogc_processes_api_url](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.ogc_processes_ui_url](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.unity_proxy_ogc_api](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/ssm_parameter) | resource |
| [kubernetes_deployment.ogc_processes_api](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/resources/deployment) | resource |
| [kubernetes_deployment.redis](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/resources/deployment) | resource |
| [kubernetes_ingress_v1.ogc_processes_api_ingress](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/resources/ingress_v1) | resource |
| [kubernetes_service.ogc_processes_api](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/resources/service) | resource |
| [kubernetes_service.redis](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/resources/service) | resource |
| [aws_db_instance.db](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/db_instance) | data source |
| [aws_lambda_functions.lambda_check_all](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/lambda_functions) | data source |
| [aws_secretsmanager_secret_version.db](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/secretsmanager_secret_version) | data source |
| [aws_ssm_parameter.subnet_ids](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/ssm_parameter) | data source |
| [kubernetes_ingress_v1.ogc_processes_api_ingress](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/data-sources/ingress_v1) | data source |
| [kubernetes_namespace.service_area](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/data-sources/namespace) | data source |
| [kubernetes_persistent_volume_claim.airflow_deployed_dags](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/data-sources/persistent_volume_claim) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_airflow_deployed_dags_pvc"></a> [airflow\_deployed\_dags\_pvc](#input\_airflow\_deployed\_dags\_pvc) | The name of the PVC for Airflow deployed DAGs | `string` | n/a | yes |
| <a name="input_airflow_webserver_password"></a> [airflow\_webserver\_password](#input\_airflow\_webserver\_password) | The password for the Airflow webserver and UI. | `string` | n/a | yes |
| <a name="input_airflow_webserver_username"></a> [airflow\_webserver\_username](#input\_airflow\_webserver\_username) | The username for the Airflow webserver and UI. | `string` | n/a | yes |
| <a name="input_dag_catalog_repo"></a> [dag\_catalog\_repo](#input\_dag\_catalog\_repo) | Git repository that stores the catalog of Airflow DAGs. | <pre>object({<br>    url                 = string<br>    ref                 = string<br>    dags_directory_path = string<br>  })</pre> | n/a | yes |
| <a name="input_db_instance_identifier"></a> [db\_instance\_identifier](#input\_db\_instance\_identifier) | The AWS DB instance identifier | `string` | n/a | yes |
| <a name="input_db_secret_arn"></a> [db\_secret\_arn](#input\_db\_secret\_arn) | The version of the database secret in AWS Secrets Manager | `string` | n/a | yes |
| <a name="input_docker_images"></a> [docker\_images](#input\_docker\_images) | Docker images for the associated services. | <pre>object({<br>    ogc_processes_api = object({<br>      name = string<br>      tag  = string<br>    })<br>    git_sync = object({<br>      name = string<br>      tag  = string<br>    })<br>    redis = object({<br>      name = string<br>      tag  = string<br>    })<br>  })</pre> | n/a | yes |
| <a name="input_karpenter_node_pools"></a> [karpenter\_node\_pools](#input\_karpenter\_node\_pools) | Names of the Karpenter node pools | `list(string)` | n/a | yes |
| <a name="input_kubernetes_namespace"></a> [kubernetes\_namespace](#input\_kubernetes\_namespace) | The kubernetes namespace for the API's resources. | `string` | n/a | yes |
| <a name="input_project"></a> [project](#input\_project) | The project or mission deploying Unity SPS | `string` | n/a | yes |
| <a name="input_release"></a> [release](#input\_release) | The software release version. | `string` | n/a | yes |
| <a name="input_service_area"></a> [service\_area](#input\_service\_area) | The service area owner of the resources being deployed | `string` | n/a | yes |
| <a name="input_venue"></a> [venue](#input\_venue) | The MCP venue in which the cluster will be deployed (dev, test, prod) | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_ogc_processes_urls"></a> [ogc\_processes\_urls](#output\_ogc\_processes\_urls) | SSM parameter IDs and URLs for the various OGC Processes endpoints. |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
