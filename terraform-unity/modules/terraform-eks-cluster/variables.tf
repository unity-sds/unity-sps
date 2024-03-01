variable "cluster_name" {
  type = string
}

variable "nodegroups" {
  description = "A map of node group configurations"

  type = map(object({
    create_iam_role            = optional(bool)
    iam_role_arn               = optional(string)
    ami_id                     = optional(string)
    min_size                   = optional(number)
    max_size                   = optional(number)
    desired_size               = optional(number)
    instance_types             = optional(list(string))
    capacity_type              = optional(string)
    enable_bootstrap_user_data = optional(bool)
    metadata_options           = optional(map(any))
  }))

  default = {
    defaultGroup = {
      instance_types = ["m5.xlarge"]
      min_size       = 1
      max_size       = 1
      desired_size   = 1
      metadata_options = {
        "http_endpoint" : "enabled",
        "http_put_response_hop_limit" : 3,
      }
    }
  }
}
