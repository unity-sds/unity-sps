
locals {
  resource_name_prefix = join("-", compact([var.project, var.venue, var.service_area, "%s"]))
}
