terraform {
  backend "s3" {
    bucket               = "unity-unity-dev-bucket"
    workspace_key_prefix = "sps/tfstates"
    key                  = "terraform.tfstate"
    region               = "us-west-2"
    encrypt              = true
  }
}

resource "kubernetes_namespace" "service_area" {
  metadata {
    name = var.service_area
  }
}

module "unity-sps-database" {
  source       = "./modules/terraform-unity-sps-database"
  project      = var.project
  venue        = var.venue
  service_area = var.service_area
  release      = var.release
}

module "unity-sps-efs" {
  source       = "./modules/terraform-unity-sps-efs"
  project      = var.project
  venue        = var.venue
  service_area = var.service_area
  release      = var.release
}

module "unity-sps-s3" {
  source       = "./modules/terraform-unity-sps-s3"
  project      = var.project
  venue        = var.venue
  service_area = var.service_area
  release      = var.release
}

module "unity-sps-karpenter-node-config" {
  source                 = "./modules/terraform-unity-sps-karpenter-node-config"
  project                = var.project
  venue                  = var.venue
  service_area           = var.service_area
  release                = var.release
  kubeconfig_filepath    = var.kubeconfig_filepath
  mcp_ami_owner_id       = var.mcp_ami_owner_id
  karpenter_node_classes = var.karpenter_node_classes
  karpenter_node_pools   = var.karpenter_node_pools
}

module "unity-sps-airflow" {
  source                     = "./modules/terraform-unity-sps-airflow"
  project                    = var.project
  venue                      = var.venue
  service_area               = var.service_area
  release                    = var.release
  kubeconfig_filepath        = var.kubeconfig_filepath
  kubernetes_namespace       = kubernetes_namespace.service_area.metadata[0].name
  db_instance_identifier     = module.unity-sps-database.db_instance_identifier
  db_secret_arn              = module.unity-sps-database.db_secret_arn
  efs_file_system_id         = module.unity-sps-efs.file_system_id
  airflow_webserver_username = var.airflow_webserver_username
  airflow_webserver_password = var.airflow_webserver_password
  docker_images              = var.airflow_docker_images
  helm_charts                = var.helm_charts
  helm_values_template       = var.helm_values_template
  karpenter_node_pools       = module.unity-sps-karpenter-node-config.karpenter_node_pools
}

module "unity-sps-ogc-processes-api" {
  source                     = "./modules/terraform-unity-sps-ogc-processes-api"
  project                    = var.project
  venue                      = var.venue
  service_area               = var.service_area
  release                    = var.release
  kubernetes_namespace       = kubernetes_namespace.service_area.metadata[0].name
  db_instance_identifier     = module.unity-sps-database.db_instance_identifier
  db_secret_arn              = module.unity-sps-database.db_secret_arn
  airflow_deployed_dags_pvc  = module.unity-sps-airflow.airflow_deployed_dags_pvc
  airflow_webserver_username = var.airflow_webserver_username
  airflow_webserver_password = var.airflow_webserver_password
  docker_images              = var.ogc_processes_docker_images
  dag_catalog_repo           = var.dag_catalog_repo
  karpenter_node_pools       = module.unity-sps-karpenter-node-config.karpenter_node_pools
}

module "unity-sps-initiators" {
  source                          = "./modules/terraform-unity-sps-initiators"
  project                         = var.project
  venue                           = var.venue
  service_area                    = var.service_area
  release                         = var.release
  airflow_api_url_ssm_param       = module.unity-sps-airflow.airflow_urls["rest_api"].ssm_param_id
  airflow_webserver_username      = var.airflow_webserver_username
  airflow_webserver_password      = var.airflow_webserver_password
  ogc_processes_api_url_ssm_param = module.unity-sps-ogc-processes-api.ogc_processes_urls["rest_api"].ssm_param_id
}
