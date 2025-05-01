# terraform-unity-sps-s3

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.8.2 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | 5.67.0 |
| <a name="requirement_helm"></a> [helm](#requirement\_helm) | 2.15.0 |
| <a name="requirement_kubernetes"></a> [kubernetes](#requirement\_kubernetes) | 2.32.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.67.0 |
| <a name="provider_helm"></a> [helm](#provider\_helm) | 2.15.0 |
| <a name="provider_kubernetes"></a> [kubernetes](#provider\_kubernetes) | 2.36.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_s3_bucket.s3_pv_bucket](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket_policy.s3_pv_bucket_policy](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/s3_bucket_policy) | resource |
| [aws_ssm_parameter.s3_pv_bucket_ssm_parameter](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/ssm_parameter) | resource |
| [helm_release.csi_s3](https://registry.terraform.io/providers/hashicorp/helm/2.15.0/docs/resources/release) | resource |
| [kubernetes_persistent_volume.s3_pv](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/resources/persistent_volume) | resource |
| [kubernetes_persistent_volume_claim.s3_pvc](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/resources/persistent_volume_claim) | resource |
| [kubernetes_storage_class.s3](https://registry.terraform.io/providers/hashicorp/kubernetes/2.32.0/docs/resources/storage_class) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_aws_region"></a> [aws\_region](#input\_aws\_region) | The AWS region of the SPS installation | `string` | `"us-west-2"` | no |
| <a name="input_kubernetes_namespace"></a> [kubernetes\_namespace](#input\_kubernetes\_namespace) | The Kubernetes namespace of the SPS installation | `string` | `"sps"` | no |
| <a name="input_project"></a> [project](#input\_project) | The project or mission deploying Unity SPS | `string` | n/a | yes |
| <a name="input_release"></a> [release](#input\_release) | The software release version | `string` | n/a | yes |
| <a name="input_service_area"></a> [service\_area](#input\_service\_area) | The service area owner of the resources being deployed | `string` | n/a | yes |
| <a name="input_venue"></a> [venue](#input\_venue) | The MCP venue in which the cluster will be deployed (dev, test, prod) | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_se_pv_bucket_name"></a> [se\_pv\_bucket\_name](#output\_se\_pv\_bucket\_name) | n/a |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
