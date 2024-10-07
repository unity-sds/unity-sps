# terraform-unity-sps-airflow

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.8.2 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | 5.50.0 |
| <a name="requirement_helm"></a> [helm](#requirement\_helm) | 2.13.1 |
| <a name="requirement_kubernetes"></a> [kubernetes](#requirement\_kubernetes) | 2.29.0 |
| <a name="requirement_null"></a> [null](#requirement\_null) | 3.2.2 |
| <a name="requirement_random"></a> [random](#requirement\_random) | 3.6.1 |
| <a name="requirement_time"></a> [time](#requirement\_time) | 0.11.1 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.50.0 |
| <a name="provider_helm"></a> [helm](#provider\_helm) | 2.13.1 |
| <a name="provider_kubernetes"></a> [kubernetes](#provider\_kubernetes) | 2.29.0 |
| <a name="provider_null"></a> [null](#provider\_null) | 3.2.2 |
| <a name="provider_random"></a> [random](#provider\_random) | 3.6.1 |
| <a name="provider_time"></a> [time](#provider\_time) | 0.11.1 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_efs_access_point.airflow_deployed_dags](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/efs_access_point) | resource |
| [aws_efs_access_point.airflow_kpo](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/efs_access_point) | resource |
| [aws_efs_mount_target.airflow](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/efs_mount_target) | resource |
| [aws_iam_policy.airflow_worker_policy](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/iam_policy) | resource |
| [aws_iam_role.airflow_worker_role](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/iam_role) | resource |
| [aws_iam_role_policy_attachment.airflow_worker_policy_attachment](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/iam_role_policy_attachment) | resource |
| [aws_lambda_invocation.unity_proxy_lambda_invocation](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/lambda_invocation) | resource |
| [aws_s3_bucket.airflow_logs](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/s3_bucket) | resource |
| [aws_security_group.airflow_efs](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/security_group) | resource |
| [aws_security_group.airflow_ingress_sg](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/security_group) | resource |
| [aws_security_group.airflow_ingress_sg_internal](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/security_group) | resource |
| [aws_security_group_rule.airflow_efs](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/security_group_rule) | resource |
| [aws_ssm_parameter.airflow_api_health_check_endpoint](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.airflow_api_url](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.airflow_logs](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.airflow_ui_health_check_endpoint](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.airflow_ui_url](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.unity_proxy_airflow_ui](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/ssm_parameter) | resource |
| [aws_vpc_security_group_ingress_rule.airflow_ingress_sg_jpl_rule](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.airflow_ingress_sg_proxy_rule](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/vpc_security_group_ingress_rule) | resource |
| [helm_release.airflow](https://registry.terraform.io/providers/hashicorp/helm/2.13.1/docs/resources/release) | resource |
| [helm_release.keda](https://registry.terraform.io/providers/hashicorp/helm/2.13.1/docs/resources/release) | resource |
| [kubernetes_ingress_v1.airflow_ingress](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/ingress_v1) | resource |
| [kubernetes_ingress_v1.airflow_ingress_internal](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/ingress_v1) | resource |
| [kubernetes_namespace.keda](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/namespace) | resource |
| [kubernetes_persistent_volume.airflow_deployed_dags](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/persistent_volume) | resource |
| [kubernetes_persistent_volume.airflow_kpo](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/persistent_volume) | resource |
| [kubernetes_persistent_volume_claim.airflow_deployed_dags](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/persistent_volume_claim) | resource |
| [kubernetes_persistent_volume_claim.airflow_kpo](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/persistent_volume_claim) | resource |
| [kubernetes_role.airflow_pod_creator](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/role) | resource |
| [kubernetes_role_binding.airflow_pod_creator_binding](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/role_binding) | resource |
| [kubernetes_secret.airflow_metadata](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/secret) | resource |
| [kubernetes_secret.airflow_webserver](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/secret) | resource |
| [kubernetes_storage_class.efs](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/storage_class) | resource |
| [null_resource.remove_keda_finalizers](https://registry.terraform.io/providers/hashicorp/null/3.2.2/docs/resources/resource) | resource |
| [random_id.airflow_webserver_secret](https://registry.terraform.io/providers/hashicorp/random/3.6.1/docs/resources/id) | resource |
| [time_sleep.wait_for_efs_mount_target_dns_propagation](https://registry.terraform.io/providers/hashicorp/time/0.11.1/docs/resources/sleep) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/caller_identity) | data source |
| [aws_db_instance.db](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/db_instance) | data source |
| [aws_efs_file_system.efs](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/efs_file_system) | data source |
| [aws_eks_cluster.cluster](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/eks_cluster) | data source |
| [aws_lambda_functions.lambda_check_all](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/lambda_functions) | data source |
| [aws_secretsmanager_secret_version.db](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/secretsmanager_secret_version) | data source |
| [aws_security_groups.venue_proxy_sg](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/security_groups) | data source |
| [aws_ssm_parameter.subnet_ids](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/ssm_parameter) | data source |
| [aws_vpc.cluster_vpc](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/vpc) | data source |
| [kubernetes_ingress_v1.airflow_ingress](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/data-sources/ingress_v1) | data source |
| [kubernetes_ingress_v1.airflow_ingress_internal](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/data-sources/ingress_v1) | data source |
| [kubernetes_namespace.service_area](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/data-sources/namespace) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_airflow_webserver_password"></a> [airflow\_webserver\_password](#input\_airflow\_webserver\_password) | The password for the Airflow webserver and UI. | `string` | n/a | yes |
| <a name="input_airflow_webserver_username"></a> [airflow\_webserver\_username](#input\_airflow\_webserver\_username) | The username for the Airflow webserver and UI. | `string` | n/a | yes |
| <a name="input_db_instance_identifier"></a> [db\_instance\_identifier](#input\_db\_instance\_identifier) | The AWS DB instance identifier | `string` | n/a | yes |
| <a name="input_db_secret_arn"></a> [db\_secret\_arn](#input\_db\_secret\_arn) | The version of the database secret in AWS Secrets Manager | `string` | n/a | yes |
| <a name="input_docker_images"></a> [docker\_images](#input\_docker\_images) | Docker images for the associated services. | <pre>object({<br>    airflow = object({<br>      name = string<br>      tag  = string<br>    })<br>  })</pre> | n/a | yes |
| <a name="input_efs_file_system_id"></a> [efs\_file\_system\_id](#input\_efs\_file\_system\_id) | The EFS file system ID | `string` | n/a | yes |
| <a name="input_helm_charts"></a> [helm\_charts](#input\_helm\_charts) | Helm charts for the associated services. | <pre>map(object({<br>    repository = string<br>    chart      = string<br>    version    = string<br>  }))</pre> | n/a | yes |
| <a name="input_karpenter_node_pools"></a> [karpenter\_node\_pools](#input\_karpenter\_node\_pools) | Names of the Karpenter node pools | `list(string)` | n/a | yes |
| <a name="input_kubeconfig_filepath"></a> [kubeconfig\_filepath](#input\_kubeconfig\_filepath) | The path to the kubeconfig file for the Kubernetes cluster. | `string` | n/a | yes |
| <a name="input_kubernetes_namespace"></a> [kubernetes\_namespace](#input\_kubernetes\_namespace) | The kubernetes namespace for Airflow resources. | `string` | n/a | yes |
| <a name="input_project"></a> [project](#input\_project) | The project or mission deploying Unity SPS | `string` | n/a | yes |
| <a name="input_release"></a> [release](#input\_release) | The software release version. | `string` | n/a | yes |
| <a name="input_service_area"></a> [service\_area](#input\_service\_area) | The service area owner of the resources being deployed | `string` | n/a | yes |
| <a name="input_venue"></a> [venue](#input\_venue) | The MCP venue in which the cluster will be deployed (dev, test, prod) | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_airflow_deployed_dags_pvc"></a> [airflow\_deployed\_dags\_pvc](#output\_airflow\_deployed\_dags\_pvc) | n/a |
| <a name="output_airflow_urls"></a> [airflow\_urls](#output\_airflow\_urls) | SSM parameter IDs and URLs for the various Airflow endpoints. |
| <a name="output_s3_buckets"></a> [s3\_buckets](#output\_s3\_buckets) | SSM parameter IDs and bucket names for the various buckets used in the pipeline. |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
