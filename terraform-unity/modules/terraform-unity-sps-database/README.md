<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.8.2 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | 5.67.0 |
| <a name="requirement_external"></a> [external](#requirement\_external) | 2.3.4 |
| <a name="requirement_kubernetes"></a> [kubernetes](#requirement\_kubernetes) | 2.32.0 |
| <a name="requirement_random"></a> [random](#requirement\_random) | 3.6.1 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.67.0 |
| <a name="provider_external"></a> [external](#provider\_external) | 2.3.4 |
| <a name="provider_random"></a> [random](#provider\_random) | 3.6.1 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_db_instance.sps_db](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/db_instance) | resource |
| [aws_db_subnet_group.db](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/db_subnet_group) | resource |
| [aws_secretsmanager_secret.db](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/secretsmanager_secret) | resource |
| [aws_secretsmanager_secret_version.db](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/secretsmanager_secret_version) | resource |
| [aws_security_group.rds_sg](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/security_group) | resource |
| [aws_security_group_rule.eks_egress_to_rds](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/security_group_rule) | resource |
| [aws_security_group_rule.rds_ingress_from_eks](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/security_group_rule) | resource |
| [random_password.db](https://registry.terraform.io/providers/hashicorp/random/3.6.1/docs/resources/password) | resource |
| [aws_db_snapshot.latest_snapshot](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/db_snapshot) | data source |
| [aws_eks_cluster.cluster](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/eks_cluster) | data source |
| [aws_security_group.default](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/security_group) | data source |
| [aws_ssm_parameter.subnet_ids](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/ssm_parameter) | data source |
| [external_external.rds_final_snapshot_exists](https://registry.terraform.io/providers/hashicorp/external/2.3.4/docs/data-sources/external) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_project"></a> [project](#input\_project) | The project or mission deploying Unity SPS | `string` | n/a | yes |
| <a name="input_release"></a> [release](#input\_release) | The software release version. | `string` | n/a | yes |
| <a name="input_service_area"></a> [service\_area](#input\_service\_area) | The service area owner of the resources being deployed | `string` | n/a | yes |
| <a name="input_venue"></a> [venue](#input\_venue) | The MCP venue in which the cluster will be deployed (dev, test, prod) | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_db_instance_identifier"></a> [db\_instance\_identifier](#output\_db\_instance\_identifier) | n/a |
| <a name="output_db_latest_snapshot"></a> [db\_latest\_snapshot](#output\_db\_latest\_snapshot) | n/a |
| <a name="output_db_secret_arn"></a> [db\_secret\_arn](#output\_db\_secret\_arn) | n/a |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
