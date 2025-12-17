
locals {
  resource_name_prefix = join("-", compact([var.project, var.venue, var.service_area, "%s"]))
  s3_bucket_name_prefix = join("-", compact([var.project, var.venue, var.service_area, "%s", "smce"]))
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
}
