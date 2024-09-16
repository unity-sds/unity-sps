variable "project" {
  description = "The project or mission deploying Unity SPS"
  type        = string
  default     = "unity"
}

variable "venue" {
  description = "The MCP venue in which the cluster will be deployed (dev, test, prod)"
  type        = string
}

variable "service_area" {
  description = "The service area owner of the resources being deployed"
  type        = string
  default     = "sps"
}

variable "release" {
  description = "The software release version."
  type        = string
  default     = "24.3"
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
    block_device_mappings = optional(map(object({
      device_name = string
      ebs = object({
        volume_size           = number
        volume_type           = string
        encrypted             = bool
        delete_on_termination = bool
      })
    })))
  }))
  default = {
    defaultGroup = {
      instance_types = ["t3.large"]
      min_size       = 1
      max_size       = 1
      desired_size   = 1
      metadata_options = {
        "http_endpoint" : "enabled",
        "http_put_response_hop_limit" : 3,
      }
      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 100
            volume_type           = "gp2"
            encrypted             = true
            delete_on_termination = true
          }
        }
      }
    }
  }
}
