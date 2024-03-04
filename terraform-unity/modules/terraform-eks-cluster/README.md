# terraform-eks-cluster

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.7.2 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | 5.35.0 |
| <a name="requirement_kubernetes"></a> [kubernetes](#requirement\_kubernetes) | 2.25.2 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.35.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_unity-eks"></a> [unity-eks](#module\_unity-eks) | git@github.com:unity-sds/unity-cs-infra.git//terraform-unity-eks_module | main |

## Resources

| Name | Type |
|------|------|
| [aws_iam_role_policy.sps_airflow_eks_inline_policy](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/resources/iam_role_policy) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/data-sources/caller_identity) | data source |
| [aws_eks_cluster.cluster](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/data-sources/eks_cluster) | data source |
| [aws_eks_cluster_auth.auth](https://registry.terraform.io/providers/hashicorp/aws/5.35.0/docs/data-sources/eks_cluster_auth) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_cluster_name"></a> [cluster\_name](#input\_cluster\_name) | n/a | `string` | n/a | yes |
| <a name="input_nodegroups"></a> [nodegroups](#input\_nodegroups) | A map of node group configurations | <pre>map(object({<br>    create_iam_role            = optional(bool)<br>    iam_role_arn               = optional(string)<br>    ami_id                     = optional(string)<br>    min_size                   = optional(number)<br>    max_size                   = optional(number)<br>    desired_size               = optional(number)<br>    instance_types             = optional(list(string))<br>    capacity_type              = optional(string)<br>    enable_bootstrap_user_data = optional(bool)<br>    metadata_options           = optional(map(any))<br>  }))</pre> | <pre>{<br>  "defaultGroup": {<br>    "desired_size": 1,<br>    "instance_types": [<br>      "m5.xlarge"<br>    ],<br>    "max_size": 1,<br>    "metadata_options": {<br>      "http_endpoint": "enabled",<br>      "http_put_response_hop_limit": 3<br>    },<br>    "min_size": 1<br>  }<br>}</pre> | no |

## Outputs

No outputs.
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
