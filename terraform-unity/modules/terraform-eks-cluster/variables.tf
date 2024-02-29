variable "cluster_name" {
  type = string
}

variable "nodegroups" {
  description = "A map of node group configurations"
  type = map(object({
    instance_types = list(string)
    min_size       = number
    max_size       = number
    desired_size   = number
  }))
  default = {
    defaultGroup = {
      instance_types = ["m5.xlarge"]
      min_size       = 1
      max_size       = 1
      desired_size   = 1
    }
  }
}
