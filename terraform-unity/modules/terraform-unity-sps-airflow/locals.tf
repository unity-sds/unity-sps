
locals {
  counter              = var.counter != "" ? var.counter : random_id.counter.hex
  resource_name_prefix = join("-", compact([var.project, var.venue, var.service_area, "%s", var.deployment_name, local.counter]))
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
  oidc_provider_url = replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")
  airflow_webserver_navbar_color = {
    "prod"    = "#bf4f4f"
    "test"    = "#cfdf4f"
    "dev"     = "#58cc35"
    "sbg-dev" = "#58cc35"
  }[var.venue]
}
