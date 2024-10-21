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

data "aws_ssm_parameter" "ssl_cert_arn" {
  name = "/unity/account/network/ssl"
}

data "aws_ssm_parameter" "ss_acct_num" {
  name = "/unity/shared-services/aws/account"
}

data "aws_ssm_parameter" "cognito_base_url" {
  name = "arn:aws:ssm:us-west-2:${data.aws_ssm_parameter.ss_acct_num.value}:parameter/unity/shared-services/cognito/base-url"
}

data "aws_ssm_parameter" "cognito_client_id" {
  name = "arn:aws:ssm:us-west-2:${data.aws_ssm_parameter.ss_acct_num.value}:parameter/unity/shared-services/cognito/airflow-ui-client-id"
}

data "aws_ssm_parameter" "cognito_client_secret" {
  name = "arn:aws:ssm:us-west-2:${data.aws_ssm_parameter.ss_acct_num.value}:parameter/unity/shared-services/cognito/airflow-ui-client-secret"
}

data "aws_ssm_parameter" "cognito_user_pool_id" {
  name = "arn:aws:ssm:us-west-2:${data.aws_ssm_parameter.ss_acct_num.value}:parameter/unity/shared-services/cognito/user-pool-id"
}