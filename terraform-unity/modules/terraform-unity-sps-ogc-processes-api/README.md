<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.8.2 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | 5.67.0 |
| <a name="requirement_kubernetes"></a> [kubernetes](#requirement\_kubernetes) | 2.32.0 |
| <a name="requirement_null"></a> [null](#requirement\_null) | 3.2.3 |
| <a name="requirement_time"></a> [time](#requirement\_time) | 0.12.1 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.67.0 |
| <a name="provider_kubernetes"></a> [kubernetes](#provider\_kubernetes) | 2.32.0 |
| <a name="provider_null"></a> [null](#provider\_null) | 3.2.4 |
| <a name="provider_time"></a> [time](#provider\_time) | 0.12.1 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_api_gateway_deployment.ogc-api-gateway-deployment](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/api_gateway_deployment) | resource |
| [aws_api_gateway_integration.rest_api_integration_for_ogc_api](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/api_gateway_integration) | resource |
| [aws_api_gateway_method.rest_api_method_for_ogc_proxy_method](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/api_gateway_method) | resource |
| [aws_api_gateway_method_response.response_200](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/api_gateway_method_response) | resource |
| [aws_api_gateway_resource.rest_api_resource_management_path](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/api_gateway_resource) | resource |
| [aws_api_gateway_resource.rest_api_resource_ogc_api_path](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/api_gateway_resource) | resource |
| [aws_api_gateway_resource.rest_api_resource_ogc_proxy_path](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/api_gateway_resource) | resource |
| [aws_api_gateway_stage.ogc-api-gateway-stage](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/api_gateway_stage) | resource |
| [aws_api_gateway_vpc_link.rest_api_ogc_vpc_link](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/api_gateway_vpc_link) | resource |
| [aws_lambda_invocation.unity_proxy_lambda_invocation](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/lambda_invocation) | resource |
| [aws_security_group.ogc_ingress_sg_internal](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/security_group) | resource |
| [aws_ssm_parameter.ogc_processes_api_health_check_endpoint](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.ogc_processes_api_url](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.ogc_processes_ui_url](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.unity_proxy_ogc_api](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/ssm_parameter) | resource |
| [aws_vpc_security_group_ingress_rule.ogc_api_ingress_sg_proxy_rule](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.ogc_ingress_sg_proxy_rule](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/vpc_security_group_ingress_rule) | resource |
| [kubernetes_deployment.ogc_processes_api](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/resources/deployment) | resource |
| [kubernetes_deployment.redis](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/resources/deployment) | resource |
| [kubernetes_service.ogc_processes_api](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/resources/service) | resource |
| [kubernetes_service.ogc_processes_api_ingress_internal](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/resources/service) | resource |
| [kubernetes_service.redis](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/resources/service) | resource |
| [null_resource.check_ogc_api_status](https://registry.terraform.io/providers/hashicorp/null/3.2.3/docs/resources/resource) | resource |
| [null_resource.register_ogc_processes](https://registry.terraform.io/providers/hashicorp/null/3.2.3/docs/resources/resource) | resource |
| [time_sleep.wait_for_gateway_integration](https://registry.terraform.io/providers/hashicorp/time/0.12.1/docs/resources/sleep) | resource |
| [time_sleep.wait_for_ogc_lb](https://registry.terraform.io/providers/hashicorp/time/0.12.1/docs/resources/sleep) | resource |
| [aws_api_gateway_authorizer.unity_cs_common_authorizer](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/api_gateway_authorizer) | data source |
| [aws_api_gateway_authorizers.unity_cs_common_authorizers_list](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/api_gateway_authorizers) | data source |
| [aws_api_gateway_rest_api.rest_api](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/api_gateway_rest_api) | data source |
| [aws_db_instance.db](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/db_instance) | data source |
| [aws_eks_cluster.cluster](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/eks_cluster) | data source |
| [aws_lambda_functions.lambda_check_all](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/lambda_functions) | data source |
| [aws_lb.ogc_k8s_lb](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/lb) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/region) | data source |
| [aws_secretsmanager_secret_version.db](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/secretsmanager_secret_version) | data source |
| [aws_security_groups.venue_proxy_sg](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/security_groups) | data source |
| [aws_ssm_parameter.shared_services_account](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/ssm_parameter) | data source |
| [aws_ssm_parameter.shared_services_domain](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/ssm_parameter) | data source |
| [aws_ssm_parameter.shared_services_region](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/ssm_parameter) | data source |
| [aws_ssm_parameter.subnet_ids](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/ssm_parameter) | data source |
| [aws_ssm_parameter.unity_client_id](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/ssm_parameter) | data source |
| [aws_ssm_parameter.unity_password](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/ssm_parameter) | data source |
| [aws_ssm_parameter.unity_username](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/ssm_parameter) | data source |
| [aws_ssm_parameter.venue_proxy_baseurl](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/ssm_parameter) | data source |
| [aws_vpc.cluster_vpc](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/vpc) | data source |
| [kubernetes_namespace.service_area](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/data-sources/namespace) | data source |
| [kubernetes_persistent_volume_claim.airflow_deployed_dags](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/data-sources/persistent_volume_claim) | data source |
| [kubernetes_service.ogc_processes_api_ingress_internal](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/data-sources/service) | data source |

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
| <a name="output_ogc_processes_venue_urls"></a> [ogc\_processes\_venue\_urls](#output\_ogc\_processes\_venue\_urls) | URLs for the various OGC Processes endpoints at venue-proxy level. |
<!-- END_TF_DOCS -->
