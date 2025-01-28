
locals {
  resource_name_prefix = join("-", compact([var.project, var.venue, var.service_area, "%s"]))
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
  load_balancer_port                  = 5000
  oidc_provider_url                   = replace(data.aws_eks_cluster.cluster.identity[0].oidc[0].issuer, "https://", "")
  airflow_metadata_kubernetes_secret  = "airflow-metadata-secret"
  airflow_webserver_kubernetes_secret = "airflow-webserver-secret"
  airflow_webserver_navbar_color = {
    "ops"     = "#bf4f4f"
    "prod"    = "#bf4f4f"
    "test"    = "#cfdf4f"
    "int"     = "#cfdf4f"
    "dev"     = "#58cc35"
    "sbg-dev" = "#58cc35"
  }[var.venue]
}
