
locals {
  resource_name_prefix  = join("-", compact([var.project, var.venue, var.service_area, "%s"]))
  s3_bucket_name_prefix = join("-", compact([var.project, var.venue, var.service_area, "%s", "smce"]))
  dag_catalog_config_bucket = "mdps-airflow-${var.venue}-dag-sources"
  common_tags = {
    Name        = ""
    Venue       = var.venue
    Proj        = var.project
    ServiceArea = var.service_area
    CapVersion  = var.release
    Component   = ""
    CreatedBy   = var.service_area
    Env         = var.venue
    mission     = var.project
    Stack       = ""
  }
  load_balancer_port = 5001
  region             = data.aws_region.current.name
  oidc_provider_url  = replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")
}
