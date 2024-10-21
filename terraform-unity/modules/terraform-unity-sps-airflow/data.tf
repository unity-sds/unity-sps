data "aws_caller_identity" "current" {}

data "aws_eks_cluster" "cluster" {
  name = format(local.resource_name_prefix, "eks")
}

data "aws_vpc" "cluster_vpc" {
  id = data.aws_eks_cluster.cluster.vpc_config[0].vpc_id
}

data "aws_ssm_parameter" "subnet_ids" {
  name = "/unity/account/network/subnet_list"
}

data "kubernetes_namespace" "service_area" {
  metadata {
    name = var.kubernetes_namespace
  }
}

data "kubernetes_ingress_v1" "airflow_ingress" {
  metadata {
    name      = kubernetes_ingress_v1.airflow_ingress.metadata[0].name
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
}

data "kubernetes_ingress_v1" "airflow_ingress_internal" {
  metadata {
    name      = kubernetes_ingress_v1.airflow_ingress_internal.metadata[0].name
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
}

data "aws_db_instance" "db" {
  db_instance_identifier = var.db_instance_identifier
}

data "aws_secretsmanager_secret_version" "db" {
  secret_id = var.db_secret_arn
}

data "aws_efs_file_system" "efs" {
  file_system_id = var.efs_file_system_id
}

data "aws_ssm_parameter" "cognito_base_url" {
  name = "/unity/shared-services/cognito/domain"
}

data "aws_ssm_parameter" "cognito_client_id" {
  name = "/unity/dev/sps/cognito_client_id"
}

data "aws_ssm_parameter" "cognito_client_secret" {
  name = "/unity/dev/sps/cognito_client_secret"
}

data "aws_ssm_parameter" "cognito_user_pool_id" {
  name = "/unity/cs/security/shared-services-cognito-user-pool/user-pool-id"
}
