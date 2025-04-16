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

/* Note: re-enable this to allow access via the JPL network
data "kubernetes_ingress_v1" "airflow_ingress" {
  metadata {
    name      = kubernetes_ingress_v1.airflow_ingress.metadata[0].name
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
}*/

data "kubernetes_service" "airflow_ingress_internal" {
  metadata {
    name      = kubernetes_service.airflow_ingress_internal.metadata[0].name
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

/* Note: re-enable this to allow access via the JPL network
data "aws_ssm_parameter" "ssl_cert_arn" {
  name = "/unity/account/network/ssl"
}*/

data "aws_ssm_parameter" "shared_services_account" {
  name = "/unity/shared-services/aws/account"
}

data "aws_ssm_parameter" "shared_services_region" {
  name = "/unity/shared-services/aws/account/region"
}

data "aws_ssm_parameter" "shared_services_domain" {
  name = "arn:aws:ssm:${data.aws_ssm_parameter.shared_services_region.value}:${data.aws_ssm_parameter.shared_services_account.value}:parameter/unity/shared-services/domain"
}

data "aws_ssm_parameter" "venue_proxy_baseurl" {
  name = "/unity/${var.project}/${var.venue}/management/httpd/loadbalancer-url"
}

data "aws_api_gateway_rest_api" "rest_api" {
  name = "unity-${var.project}-${var.venue}-rest-api-gateway"
}

data "aws_api_gateway_authorizers" "unity_cs_common_authorizers_list" {
  rest_api_id = data.aws_api_gateway_rest_api.rest_api.id
}

data "aws_api_gateway_authorizer" "unity_cs_common_authorizer" {
  rest_api_id   = data.aws_api_gateway_rest_api.rest_api.id
  authorizer_id = data.aws_api_gateway_authorizers.unity_cs_common_authorizers_list.ids[0]
}

data "aws_lb" "airflow_k8s_lb" {
  tags = {
    Venue = var.venue
    Proj  = var.project
    Name  = format(local.resource_name_prefix, "AirflowLB")
    Stack = "airflow"
  }
  depends_on = [kubernetes_service.airflow_ingress_internal]
}

data "aws_lambda_functions" "lambda_check_all" {}

data "aws_security_groups" "venue_proxy_sg" {
  filter {
    name   = "group-name"
    values = ["${var.project}-${var.venue}-ecs_service_sg"]
  }
  tags = {
    Service = "U-CS"
  }
}
