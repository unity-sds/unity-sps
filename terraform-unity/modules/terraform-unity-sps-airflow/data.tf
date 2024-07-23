data "aws_caller_identity" "current" {}

data "aws_eks_cluster" "cluster" {
  name = format(local.resource_name_prefix, "eks")
}

data "aws_eks_cluster_auth" "cluster" {
  name = format(local.resource_name_prefix, "eks")
}

data "aws_vpc" "cluster_vpc" {
  id = data.aws_eks_cluster.cluster.vpc_config[0].vpc_id
}

data "aws_ssm_parameter" "subnet_ids" {
  name = "/unity/cs/account/network/subnet_list"
}

data "aws_ssm_parameter" "al2_eks_optimized_ami" {
  name = "/mcp/amis/aml2-eks-${replace(data.aws_eks_cluster.cluster.version, ".", "-")}"
}

data "aws_iam_role" "cluster_iam_role" {
  name = "${format(local.resource_name_prefix, "eks")}-eks-node-role"
}

data "aws_security_group" "default" {
  vpc_id = data.aws_eks_cluster.cluster.vpc_config[0].vpc_id
  filter {
    name   = "tag:Name"
    values = ["${format(local.resource_name_prefix, "eks")}-node"]
  }
}

data "aws_ssm_parameter" "ssl_cert_arn" {
  name = "/unity/account/network/ssl"
}

data "kubernetes_ingress_v1" "airflow_ingress" {
  metadata {
    name      = kubernetes_ingress_v1.airflow_ingress.metadata[0].name
    namespace = kubernetes_namespace.airflow.metadata[0].name
  }
}

data "kubernetes_ingress_v1" "ogc_processes_api_ingress" {
  metadata {
    name      = kubernetes_ingress_v1.ogc_processes_api_ingress.metadata[0].name
    namespace = kubernetes_namespace.airflow.metadata[0].name
  }
}


data "aws_ami" "al2_eks_optimized" {
  filter {
    name   = "image-id"
    values = [data.aws_ssm_parameter.al2_eks_optimized_ami.value]
  }
  owners = [var.mcp_ami_owner_id]
}
