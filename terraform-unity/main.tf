module "unity-sps-airflow" {
  source                      = "./modules/terraform-unity-sps-airflow"
  project                     = var.project
  venue                       = var.venue
  service_area                = var.service_area
  counter                     = var.counter
  release                     = var.release
  eks_cluster_name            = var.eks_cluster_name
  kubeconfig_filepath         = var.kubeconfig_filepath
  airflow_webserver_password  = var.airflow_webserver_password
  custom_airflow_docker_image = var.custom_airflow_docker_image
  helm_charts                 = var.helm_charts
}
