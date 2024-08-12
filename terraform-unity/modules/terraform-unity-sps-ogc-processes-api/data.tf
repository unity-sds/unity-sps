data "kubernetes_namespace" "service_area" {
  metadata {
    name = var.kubernetes_namespace
  }
}

data "aws_ssm_parameter" "ssl_cert_arn" {
  name = "/unity/account/network/ssl"
}

data "aws_ssm_parameter" "subnet_ids" {
  name = "/unity/cs/account/network/subnet_list"
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

data "kubernetes_ingress_v1" "ogc_processes_api_ingress" {
  metadata {
    name      = kubernetes_ingress_v1.ogc_processes_api_ingress.metadata[0].name
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
}
