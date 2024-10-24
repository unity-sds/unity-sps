<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.8.2 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | 5.47.0 |
| <a name="requirement_helm"></a> [helm](#requirement\_helm) | 2.13.1 |
| <a name="requirement_kubernetes"></a> [kubernetes](#requirement\_kubernetes) | 2.29.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.47.0 |
| <a name="provider_helm"></a> [helm](#provider\_helm) | 2.13.1 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_karpenter"></a> [karpenter](#module\_karpenter) | terraform-aws-modules/eks/aws//modules/karpenter | 20.8.5 |

## Resources

| Name | Type |
|------|------|
| [helm_release.karpenter](https://registry.terraform.io/providers/hashicorp/helm/2.13.1/docs/resources/release) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/5.47.0/docs/data-sources/caller_identity) | data source |
| [aws_eks_cluster.cluster](https://registry.terraform.io/providers/hashicorp/aws/5.47.0/docs/data-sources/eks_cluster) | data source |
| [aws_eks_cluster_auth.cluster](https://registry.terraform.io/providers/hashicorp/aws/5.47.0/docs/data-sources/eks_cluster_auth) | data source |
| [aws_iam_role.cluster_iam_role](https://registry.terraform.io/providers/hashicorp/aws/5.47.0/docs/data-sources/iam_role) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_helm_charts"></a> [helm\_charts](#input\_helm\_charts) | Helm charts for the associated services. | <pre>map(object({<br>    repository = string<br>    chart      = string<br>    version    = string<br>  }))</pre> | <pre>{<br>  "karpenter": {<br>    "chart": "karpenter",<br>    "repository": "oci://public.ecr.aws/karpenter",<br>    "version": "0.36.1"<br>  }<br>}</pre> | no |
| <a name="input_project"></a> [project](#input\_project) | The project or mission deploying Unity SPS | `string` | `"unity"` | no |
| <a name="input_release"></a> [release](#input\_release) | The software release version. | `string` | `"24.3"` | no |
| <a name="input_service_area"></a> [service\_area](#input\_service\_area) | The service area owner of the resources being deployed | `string` | `"sps"` | no |
| <a name="input_venue"></a> [venue](#input\_venue) | The MCP venue in which the cluster will be deployed (dev, test, prod) | `string` | n/a | yes |

## Outputs

No outputs.
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
