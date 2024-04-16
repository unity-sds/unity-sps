module "unity-sps-airflow" {
  source                                   = "./modules/terraform-unity-sps-airflow"
  project                                  = var.project
  venue                                    = var.venue
  service_area                             = var.service_area
  deployment_name                          = var.deployment_name
  counter                                  = var.counter
  release                                  = var.release
  kubeconfig_filepath                      = var.kubeconfig_filepath
  airflow_webserver_password               = var.airflow_webserver_password
  docker_images                            = var.docker_images
  helm_charts                              = var.helm_charts
  mcp_al2_eks_optimized_ami                = var.mcp_al2_eks_optimized_ami
  karpenter_default_node_pool_requirements = var.karpenter_default_node_pool_requirements
  karpenter_default_node_pool_limits       = var.karpenter_default_node_pool_limits
  karpenter_default_node_pool_disruption   = var.karpenter_default_node_pool_disruption
}
