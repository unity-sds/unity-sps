# terraform-unity-sps-airflow

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

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.43.0 |
| <a name="provider_helm"></a> [helm](#provider\_helm) | 2.12.1 |
| <a name="provider_kubectl"></a> [kubectl](#provider\_kubectl) | 2.0.4 |
| <a name="provider_kubernetes"></a> [kubernetes](#provider\_kubernetes) | 2.25.2 |
| <a name="provider_null"></a> [null](#provider\_null) | 3.2.2 |
| <a name="provider_random"></a> [random](#provider\_random) | 3.6.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_karpenter"></a> [karpenter](#module\_karpenter) | terraform-aws-modules/eks/aws//modules/karpenter | 20.8.4 |

## Resources

| Name | Type |
|------|------|
| [aws_cloudwatch_log_group.airflow_dag_trigger](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/cloudwatch_log_group) | resource |
| [aws_db_instance.airflow_db](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/db_instance) | resource |
| [aws_db_subnet_group.airflow_db](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/db_subnet_group) | resource |
| [aws_efs_access_point.airflow_kpo](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/efs_access_point) | resource |
| [aws_efs_file_system.airflow_kpo](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/efs_file_system) | resource |
| [aws_efs_mount_target.airflow_kpo](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/efs_mount_target) | resource |
| [aws_iam_policy.airflow_worker_policy](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/iam_policy) | resource |
| [aws_iam_policy.lambda_sqs_access](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/iam_policy) | resource |
| [aws_iam_role.airflow_worker_role](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/iam_role) | resource |
| [aws_iam_role.lambda](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/iam_role) | resource |
| [aws_iam_role_policy_attachment.airflow_worker_policy_attachment](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.lambda_logs](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.lambda_sqs_access_attach](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/iam_role_policy_attachment) | resource |
| [aws_lambda_event_source_mapping.lambda_airflow_dag_trigger](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/lambda_event_source_mapping) | resource |
| [aws_lambda_function.airflow_dag_trigger](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/lambda_function) | resource |
| [aws_s3_bucket.airflow_logs](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket.inbound_staging_location](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket.lambdas](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket_notification.isl_bucket_notification](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/s3_bucket_notification) | resource |
| [aws_s3_object.lambdas](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/s3_object) | resource |
| [aws_secretsmanager_secret.airflow_db](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/secretsmanager_secret) | resource |
| [aws_secretsmanager_secret_version.airflow_db](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/secretsmanager_secret_version) | resource |
| [aws_security_group.airflow_kpo_efs](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/security_group) | resource |
| [aws_security_group.rds_sg](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/security_group) | resource |
| [aws_security_group_rule.airflow_kpo_efs](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/security_group_rule) | resource |
| [aws_security_group_rule.eks_egress_to_rds](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/security_group_rule) | resource |
| [aws_security_group_rule.rds_ingress_from_eks](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/security_group_rule) | resource |
| [aws_sns_topic.s3_isl_event_topic](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/sns_topic) | resource |
| [aws_sns_topic_policy.s3_isl_event_topic_policy](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/sns_topic_policy) | resource |
| [aws_sns_topic_subscription.s3_isl_event_subscription](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/sns_topic_subscription) | resource |
| [aws_sqs_queue.s3_isl_event_queue](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/sqs_queue) | resource |
| [aws_sqs_queue_policy.s3_isl_event_queue_policy](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/sqs_queue_policy) | resource |
| [aws_ssm_parameter.airflow_api_url](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.airflow_dag_trigger_lambda_package](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.airflow_logs](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.airflow_ui_url](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.isl_bucket](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.ogc_processes_api_url](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/resources/ssm_parameter) | resource |
| [helm_release.airflow](https://registry.terraform.io/providers/hashicorp/helm/2.12.1/docs/resources/release) | resource |
| [helm_release.karpenter](https://registry.terraform.io/providers/hashicorp/helm/2.12.1/docs/resources/release) | resource |
| [helm_release.keda](https://registry.terraform.io/providers/hashicorp/helm/2.12.1/docs/resources/release) | resource |
| [kubectl_manifest.karpenter_example_deployment](https://registry.terraform.io/providers/alekc/kubectl/2.0.4/docs/resources/manifest) | resource |
| [kubectl_manifest.karpenter_node_class](https://registry.terraform.io/providers/alekc/kubectl/2.0.4/docs/resources/manifest) | resource |
| [kubectl_manifest.karpenter_node_pool](https://registry.terraform.io/providers/alekc/kubectl/2.0.4/docs/resources/manifest) | resource |
| [kubernetes_deployment.ogc_processes_api](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/deployment) | resource |
| [kubernetes_ingress_v1.airflow_ingress](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/ingress_v1) | resource |
| [kubernetes_ingress_v1.ogc_processes_api_ingress](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/ingress_v1) | resource |
| [kubernetes_namespace.airflow](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/namespace) | resource |
| [kubernetes_namespace.keda](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/namespace) | resource |
| [kubernetes_persistent_volume.efs_pv](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/persistent_volume) | resource |
| [kubernetes_persistent_volume_claim.efs_pvc](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/persistent_volume_claim) | resource |
| [kubernetes_role.airflow_pod_creator](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/role) | resource |
| [kubernetes_role_binding.airflow_pod_creator_binding](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/role_binding) | resource |
| [kubernetes_secret.airflow_metadata](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/secret) | resource |
| [kubernetes_secret.airflow_webserver](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/secret) | resource |
| [kubernetes_service.ogc_processes_api](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/service) | resource |
| [kubernetes_storage_class.efs](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/storage_class) | resource |
| [null_resource.build_lambda_packages](https://registry.terraform.io/providers/hashicorp/null/3.2.2/docs/resources/resource) | resource |
| [null_resource.remove_finalizers](https://registry.terraform.io/providers/hashicorp/null/3.2.2/docs/resources/resource) | resource |
| [random_id.airflow_webserver_secret](https://registry.terraform.io/providers/hashicorp/random/3.6.0/docs/resources/id) | resource |
| [random_id.counter](https://registry.terraform.io/providers/hashicorp/random/3.6.0/docs/resources/id) | resource |
| [random_password.airflow_db](https://registry.terraform.io/providers/hashicorp/random/3.6.0/docs/resources/password) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/data-sources/caller_identity) | data source |
| [aws_eks_cluster.cluster](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/data-sources/eks_cluster) | data source |
| [aws_eks_cluster_auth.cluster](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/data-sources/eks_cluster_auth) | data source |
| [aws_eks_node_group.default_group](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/data-sources/eks_node_group) | data source |
| [aws_security_group.default](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/data-sources/security_group) | data source |
| [aws_ssm_parameter.subnet_ids](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/data-sources/ssm_parameter) | data source |
| [aws_vpc.cluster_vpc](https://registry.terraform.io/providers/hashicorp/aws/5.43.0/docs/data-sources/vpc) | data source |
| [kubernetes_ingress_v1.airflow_ingress](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/data-sources/ingress_v1) | data source |
| [kubernetes_ingress_v1.ogc_processes_api_ingress](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/data-sources/ingress_v1) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_airflow_webserver_password"></a> [airflow\_webserver\_password](#input\_airflow\_webserver\_password) | The password for the Airflow webserver and UI. | `string` | n/a | yes |
| <a name="input_counter"></a> [counter](#input\_counter) | Identifier used to uniquely distinguish resources. This is used in the naming convention of the resource. If left empty, a random hexadecimal value will be generated and used instead. | `string` | n/a | yes |
| <a name="input_deployment_name"></a> [deployment\_name](#input\_deployment\_name) | The name of the deployment. | `string` | n/a | yes |
| <a name="input_docker_images"></a> [docker\_images](#input\_docker\_images) | Docker images for the associated services. | <pre>object({<br>    airflow = object({<br>      name = string<br>      tag  = string<br>    }),<br>    ogc_processes_api = object({<br>      name = string<br>      tag  = string<br>    })<br>  })</pre> | n/a | yes |
| <a name="input_helm_charts"></a> [helm\_charts](#input\_helm\_charts) | Helm charts for the associated services. | <pre>map(object({<br>    repository = string<br>    chart      = string<br>    version    = string<br>  }))</pre> | n/a | yes |
| <a name="input_kubeconfig_filepath"></a> [kubeconfig\_filepath](#input\_kubeconfig\_filepath) | The path to the kubeconfig file for the Kubernetes cluster. | `string` | n/a | yes |
| <a name="input_project"></a> [project](#input\_project) | The project or mission deploying Unity SPS | `string` | n/a | yes |
| <a name="input_release"></a> [release](#input\_release) | The software release version. | `string` | n/a | yes |
| <a name="input_service_area"></a> [service\_area](#input\_service\_area) | The service area owner of the resources being deployed | `string` | n/a | yes |
| <a name="input_venue"></a> [venue](#input\_venue) | The MCP venue in which the cluster will be deployed (dev, test, prod) | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_airflow_urls"></a> [airflow\_urls](#output\_airflow\_urls) | SSM parameter IDs and URLs for the various Airflow endpoints. |
| <a name="output_ogc_processes_api_url"></a> [ogc\_processes\_api\_url](#output\_ogc\_processes\_api\_url) | SSM parameter IDs and URLs for the OGC Processes API endpoint. |
| <a name="output_s3_buckets"></a> [s3\_buckets](#output\_s3\_buckets) | SSM parameter IDs and bucket names for the various buckets used in the pipeline. |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
