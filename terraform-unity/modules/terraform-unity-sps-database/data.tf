data "aws_eks_cluster" "cluster" {
  name = format(local.resource_name_prefix, "eks")
}

data "aws_ssm_parameter" "subnet_ids" {
  name = "/unity/cs/account/network/subnet_list"
}

data "aws_security_group" "default" {
  vpc_id = data.aws_eks_cluster.cluster.vpc_config[0].vpc_id
  filter {
    name   = "tag:Name"
    values = ["${format(local.resource_name_prefix, "eks")}-node"]
  }
}
