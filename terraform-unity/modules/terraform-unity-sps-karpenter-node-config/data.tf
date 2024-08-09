data "aws_eks_cluster" "cluster" {
  name = format(local.resource_name_prefix, "eks")
}

data "aws_iam_role" "cluster_iam_role" {
  name = "${format(local.resource_name_prefix, "eks")}-eks-node-role"
}

data "aws_ssm_parameter" "subnet_ids" {
  name = "/unity/cs/account/network/subnet_list"
}

data "aws_ssm_parameter" "al2_eks_optimized_ami" {
  name = "/mcp/amis/aml2-eks-${replace(data.aws_eks_cluster.cluster.version, ".", "-")}"
}

data "aws_ami" "al2_eks_optimized" {
  filter {
    name   = "image-id"
    values = [data.aws_ssm_parameter.al2_eks_optimized_ami.value]
  }
  owners = [var.mcp_ami_owner_id]
}
