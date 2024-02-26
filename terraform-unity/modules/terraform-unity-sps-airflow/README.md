# terraform-unity-sps-airflow

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.7.2 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | 5.35.0 |
| <a name="requirement_helm"></a> [helm](#requirement\_helm) | 2.12.1 |
| <a name="requirement_kubernetes"></a> [kubernetes](#requirement\_kubernetes) | 2.25.2 |
| <a name="requirement_null"></a> [null](#requirement\_null) | 3.2.2 |
| <a name="requirement_random"></a> [random](#requirement\_random) | 3.6.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.36.0 |
| <a name="provider_helm"></a> [helm](#provider\_helm) | 2.12.1 |
| <a name="provider_kubernetes"></a> [kubernetes](#provider\_kubernetes) | 2.25.2 |
| <a name="provider_null"></a> [null](#provider\_null) | 3.2.2 |
| <a name="provider_random"></a> [random](#provider\_random) | 3.6.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_db_instance.airflow_db](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/resources/db_instance) | resource |
| [aws_db_subnet_group.airflow_db](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/resources/db_subnet_group) | resource |
| [aws_s3_bucket.airflow_logs](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/resources/s3_bucket) | resource |
| [aws_secretsmanager_secret.airflow_db](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/resources/secretsmanager_secret) | resource |
| [aws_secretsmanager_secret_version.airflow_db](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/resources/secretsmanager_secret_version) | resource |
| [aws_security_group.rds_sg](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/resources/security_group) | resource |
| [aws_security_group_rule.eks_egress_to_rds](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/resources/security_group_rule) | resource |
| [aws_security_group_rule.rds_ingress_from_eks](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/resources/security_group_rule) | resource |
| [helm_release.airflow](https://registry.terraform.io/providers/hashicorp/helm/2.12.1/docs/resources/release) | resource |
| [helm_release.keda](https://registry.terraform.io/providers/hashicorp/helm/2.12.1/docs/resources/release) | resource |
| [kubernetes_ingress_v1.airflow_ingress](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/ingress_v1) | resource |
| [kubernetes_namespace.airflow](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/namespace) | resource |
| [kubernetes_namespace.keda](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/namespace) | resource |
| [kubernetes_role.airflow_pod_creator](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/role) | resource |
| [kubernetes_role_binding.airflow_pod_creator_binding](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/role_binding) | resource |
| [kubernetes_secret.airflow_metadata](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/secret) | resource |
| [kubernetes_secret.airflow_webserver](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/resources/secret) | resource |
| [null_resource.remove_finalizers](https://registry.terraform.io/providers/hashicorp/null/3.2.2/docs/resources/resource) | resource |
| [random_id.airflow_webserver_secret](https://registry.terraform.io/providers/hashicorp/random/3.6.0/docs/resources/id) | resource |
| [random_id.counter](https://registry.terraform.io/providers/hashicorp/random/3.6.0/docs/resources/id) | resource |
| [random_password.airflow_db](https://registry.terraform.io/providers/hashicorp/random/3.6.0/docs/resources/password) | resource |
| [aws_eks_cluster.cluster](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/data-sources/eks_cluster) | data source |
| [aws_eks_cluster_auth.cluster](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/data-sources/eks_cluster_auth) | data source |
| [aws_eks_node_group.default](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/data-sources/eks_node_group) | data source |
| [aws_security_group.default](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/data-sources/security_group) | data source |
| [aws_ssm_parameter.subnet_ids](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/data-sources/ssm_parameter) | data source |
| [kubernetes_ingress_v1.airflow_ingress](https://registry.terraform.io/providers/hashicorp/kubernetes/2.25.2/docs/data-sources/ingress_v1) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_airflow_webserver_password"></a> [airflow\_webserver\_password](#input\_airflow\_webserver\_password) | value | `string` | n/a | yes |
| <a name="input_counter"></a> [counter](#input\_counter) | value | `string` | n/a | yes |
| <a name="input_custom_airflow_docker_image"></a> [custom\_airflow\_docker\_image](#input\_custom\_airflow\_docker\_image) | Docker image for the customized Airflow image. | <pre>object({<br>    name = string<br>    tag  = string<br>  })</pre> | n/a | yes |
| <a name="input_eks_cluster_name"></a> [eks\_cluster\_name](#input\_eks\_cluster\_name) | value | `string` | n/a | yes |
| <a name="input_helm_charts"></a> [helm\_charts](#input\_helm\_charts) | Settings for the required Helm charts. | <pre>map(object({<br>    repository = string<br>    chart      = string<br>    version    = string<br>  }))</pre> | n/a | yes |
| <a name="input_kubeconfig_filepath"></a> [kubeconfig\_filepath](#input\_kubeconfig\_filepath) | Path to the kubeconfig file for the Kubernetes cluster | `string` | n/a | yes |
| <a name="input_project"></a> [project](#input\_project) | The project or mission deploying Unity SPS | `string` | n/a | yes |
| <a name="input_release"></a> [release](#input\_release) | The SPS release version | `string` | n/a | yes |
| <a name="input_service_area"></a> [service\_area](#input\_service\_area) | The service area owner of the resources being deployed | `string` | n/a | yes |
| <a name="input_venue"></a> [venue](#input\_venue) | The MCP venue in which the cluster will be deployed (dev, test, prod) | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_airflow_webserver_url"></a> [airflow\_webserver\_url](#output\_airflow\_webserver\_url) | The URL of the Airflow webserver service |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
