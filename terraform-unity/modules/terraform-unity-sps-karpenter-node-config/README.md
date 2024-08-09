<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.8.2 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | 5.50.0 |
| <a name="requirement_kubernetes"></a> [kubernetes](#requirement\_kubernetes) | 2.29.0 |
| <a name="requirement_null"></a> [null](#requirement\_null) | 3.2.2 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.62.0 |
| <a name="provider_kubernetes"></a> [kubernetes](#provider\_kubernetes) | 2.29.0 |
| <a name="provider_null"></a> [null](#provider\_null) | 3.2.2 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [kubernetes_manifest.karpenter_node_classes](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/manifest) | resource |
| [kubernetes_manifest.karpenter_node_pools](https://registry.terraform.io/providers/hashicorp/kubernetes/2.29.0/docs/resources/manifest) | resource |
| [null_resource.remove_node_class_finalizers](https://registry.terraform.io/providers/hashicorp/null/3.2.2/docs/resources/resource) | resource |
| [aws_ami.al2_eks_optimized](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/ami) | data source |
| [aws_eks_cluster.cluster](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/eks_cluster) | data source |
| [aws_iam_role.cluster_iam_role](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/iam_role) | data source |
| [aws_ssm_parameter.al2_eks_optimized_ami](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/ssm_parameter) | data source |
| [aws_ssm_parameter.subnet_ids](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/ssm_parameter) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_karpenter_node_classes"></a> [karpenter\_node\_classes](#input\_karpenter\_node\_classes) | n/a | <pre>map(object({<br>    volume_size = string<br>  }))</pre> | n/a | yes |
| <a name="input_karpenter_node_pools"></a> [karpenter\_node\_pools](#input\_karpenter\_node\_pools) | Configuration for Karpenter node pools | <pre>map(object({<br>    requirements : list(object({<br>      key : string<br>      operator : string<br>      values : list(string)<br>    }))<br>    nodeClassRef : string<br>    limits : object({<br>      cpu : string<br>      memory : string<br>    })<br>    disruption : object({<br>      consolidationPolicy : string<br>      consolidateAfter : string<br>    })<br>  }))</pre> | n/a | yes |
| <a name="input_kubeconfig_filepath"></a> [kubeconfig\_filepath](#input\_kubeconfig\_filepath) | The path to the kubeconfig file for the Kubernetes cluster. | `string` | n/a | yes |
| <a name="input_mcp_ami_owner_id"></a> [mcp\_ami\_owner\_id](#input\_mcp\_ami\_owner\_id) | The ID of the MCP AMIs | `string` | n/a | yes |
| <a name="input_project"></a> [project](#input\_project) | The project or mission deploying Unity SPS | `string` | n/a | yes |
| <a name="input_release"></a> [release](#input\_release) | The software release version. | `string` | n/a | yes |
| <a name="input_service_area"></a> [service\_area](#input\_service\_area) | The service area owner of the resources being deployed | `string` | n/a | yes |
| <a name="input_venue"></a> [venue](#input\_venue) | The MCP venue in which the cluster will be deployed (dev, test, prod) | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_karpenter_node_class_names"></a> [karpenter\_node\_class\_names](#output\_karpenter\_node\_class\_names) | Names of the Karpenter node classes |
| <a name="output_karpenter_node_pools"></a> [karpenter\_node\_pools](#output\_karpenter\_node\_pools) | Names of the Karpenter node pools |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
