locals {
  counter              = var.counter != "" ? var.counter : random_id.counter.hex
  resource_name_prefix = join("-", compact([var.project, var.venue, var.service_area, "%s", var.deployment_name, local.counter]))
  cluster_name         = format(local.resource_name_prefix, "eks")
}
