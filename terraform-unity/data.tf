data "aws_eks_cluster" "cluster" {
  name = format(local.resource_name_prefix, "eks")
}

data "aws_eks_cluster_auth" "cluster" {
  name = format(local.resource_name_prefix, "eks")
}
