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

data "aws_iam_policy" "mcp_operator_policy" {
  name = "mcp-tenantOperator-AMI-APIG"
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com", "apigateway.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

# IAM Policy Document for Inline Policy
data "aws_iam_policy_document" "inline_policy" {
  statement {
    actions = ["logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    "lambda:InvokeFunction"]
    resources = ["*"]
  }
}

data "aws_api_gateway_vpc_link" "rest_api_unity_vpc_link" {
  name = "mc-nlb-vpc-link-${var.project}-${var.venue}"
}

data "aws_api_gateway_rest_api" "rest_api" {
  name = "unity-${var.project}-${var.venue}-rest-api-gateway"
}

# Unity CS Common Lambda Authorizer Allowed Cognito User Pool ID
data "aws_ssm_parameter" "api_gateway_cs_lambda_authorizer_cognito_user_pool_id" {
  name = "arn:aws:ssm:${data.aws_ssm_parameter.shared_services_region.value}:${data.aws_ssm_parameter.shared_services_account.value}:parameter/unity/shared-services/cognito/user-pool-id"
}

# Unity CS Common Lambda Authorizer Allowed Cognito User Groups List (Comma Seperated)
data "aws_ssm_parameter" "api_gateway_cs_lambda_authorizer_cognito_user_groups_list" {
  name = "arn:aws:ssm:${data.aws_ssm_parameter.shared_services_region.value}:${data.aws_ssm_parameter.shared_services_account.value}:parameter/unity/shared-services/cognito/default-user-groups"
}