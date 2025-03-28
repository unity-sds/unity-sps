data "kubernetes_namespace" "service_area" {
  metadata {
    name = var.kubernetes_namespace
  }
}

data "aws_eks_cluster" "cluster" {
  name = format(local.resource_name_prefix, "eks")
}

data "aws_vpc" "cluster_vpc" {
  id = data.aws_eks_cluster.cluster.vpc_config[0].vpc_id
}

data "aws_ssm_parameter" "subnet_ids" {
  name = "/unity/account/network/subnet_list"
}

data "aws_db_instance" "db" {
  db_instance_identifier = var.db_instance_identifier
}

data "aws_secretsmanager_secret_version" "db" {
  secret_id = var.db_secret_arn
}

data "kubernetes_persistent_volume_claim" "airflow_deployed_dags" {
  metadata {
    name = var.airflow_deployed_dags_pvc
  }
}

/* Note: re-enable this to allow access via the JPL network
data "kubernetes_ingress_v1" "ogc_processes_api_ingress" {
  metadata {
    name      = kubernetes_ingress_v1.ogc_processes_api_ingress.metadata[0].name
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
}*/

data "kubernetes_service" "ogc_processes_api_ingress_internal" {
  metadata {
    name      = kubernetes_service.ogc_processes_api_ingress_internal.metadata[0].name
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
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

data "aws_iam_role" "iam_for_lambda_auth" {
  name = "${var.project}-${var.venue}-iam_for_lambda_auth"
}

data "aws_lambda_function" "cs_common_lambda_auth" {
  function_name = "${var.project}-${var.venue}-${var.unity_cs_lambda_authorizer_function_name}"
}

data "aws_api_gateway_vpc_link" "rest_api_unity_vpc_link" {
  name = "mc-nlb-vpc-link-${var.project}-${var.venue}"
}

data "aws_api_gateway_rest_api" "rest_api" {
  name = "unity-${var.project}-${var.venue}-rest-api-gateway"
}

data "aws_api_gateway_authorizers" "unity_cs_common_authorizers_list" {
  rest_api_id                      = data.aws_api_gateway_rest_api.rest_api.id
}

data "aws_api_gateway_authorizer" "unity_cs_common_authorizer" {
  rest_api_id                      = data.aws_api_gateway_rest_api.rest_api.id
  authorizer_id                    = data.aws_api_gateway_authorizers.unity_cs_common_authorizers_list.ids[0]
}

data "aws_api_gateway_resource" "rest_api_resource_management_path" {
  rest_api_id = data.aws_api_gateway_rest_api.rest_api.id
  path        = "/sps"
}