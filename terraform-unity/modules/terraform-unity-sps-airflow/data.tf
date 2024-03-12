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
