# terraform-eks-cluster

<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.8.2 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | 5.67.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.67.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_unity-eks"></a> [unity-eks](#module\_unity-eks) | git@github.com:unity-sds/unity-cs-infra.git//terraform-unity-eks_module | unity-sps-2.2.0-hotfix |

## Resources

| Name | Type |
|------|------|
| [aws_iam_role_policy.sps_airflow_eks_inline_policy](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/resources/iam_role_policy) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/5.67.0/docs/data-sources/caller_identity) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_nodegroups"></a> [nodegroups](#input\_nodegroups) | A map of node group configurations | <pre>map(object({<br>    create_iam_role            = optional(bool)<br>    iam_role_arn               = optional(string)<br>    ami_id                     = optional(string)<br>    min_size                   = optional(number)<br>    max_size                   = optional(number)<br>    desired_size               = optional(number)<br>    instance_types             = optional(list(string))<br>    capacity_type              = optional(string)<br>    enable_bootstrap_user_data = optional(bool)<br>    metadata_options           = optional(map(any))<br>    block_device_mappings = optional(map(object({<br>      device_name = string<br>      ebs = object({<br>        volume_size           = number<br>        volume_type           = string<br>        encrypted             = bool<br>        delete_on_termination = bool<br>      })<br>    })))<br>  }))</pre> | <pre>{<br>  "defaultGroup": {<br>    "block_device_mappings": {<br>      "xvda": {<br>        "device_name": "/dev/xvda",<br>        "ebs": {<br>          "delete_on_termination": true,<br>          "encrypted": true,<br>          "volume_size": 100,<br>          "volume_type": "gp2"<br>        }<br>      }<br>    },<br>    "desired_size": 1,<br>    "instance_types": [<br>      "t3.xlarge"<br>    ],<br>    "max_size": 1,<br>    "metadata_options": {<br>      "http_endpoint": "enabled",<br>      "http_put_response_hop_limit": 3<br>    },<br>    "min_size": 1<br>  }<br>}</pre> | no |
| <a name="input_project"></a> [project](#input\_project) | The project or mission deploying Unity SPS | `string` | `"unity"` | no |
| <a name="input_release"></a> [release](#input\_release) | The software release version. | `string` | `"24.3"` | no |
| <a name="input_service_area"></a> [service\_area](#input\_service\_area) | The service area owner of the resources being deployed | `string` | `"sps"` | no |
| <a name="input_venue"></a> [venue](#input\_venue) | The MCP venue in which the cluster will be deployed (dev, test, prod) | `string` | n/a | yes |

## Outputs

No outputs.
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
