# S3 backend
terraform {
  backend "s3" {
    # full path to Terraform state file:
    # s3://<bucket>/<key>
    bucket = ""
    key    = ""
    region = "us-west-2"
  }
}

module "unity-sps-airflow" {
  source                     = "./modules/terraform-unity-sps-airflow"
  project                    = var.project
  venue                      = var.venue
  service_area               = var.service_area
  deployment_name            = var.deployment_name
  counter                    = var.counter
  release                    = var.release
  kubeconfig_filepath        = var.kubeconfig_filepath
  airflow_webserver_password = var.airflow_webserver_password
  docker_images              = var.docker_images
  helm_charts                = var.helm_charts
  mcp_ami_owner_id           = var.mcp_ami_owner_id
  karpenter_node_pools       = var.karpenter_node_pools
  dag_catalog_repo           = var.dag_catalog_repo
}
