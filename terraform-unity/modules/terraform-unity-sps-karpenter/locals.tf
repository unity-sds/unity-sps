
locals {
  resource_name_prefix = join("-", compact([var.project, var.venue, var.service_area, "%s"]))
  cluster_name         = format(local.resource_name_prefix, "eks")
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
}
