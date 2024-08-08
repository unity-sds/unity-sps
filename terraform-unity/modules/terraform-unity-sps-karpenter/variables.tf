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
  default     = "24.2"
}

variable "helm_charts" {
  description = "Helm charts for the associated services."
  type = map(object({
    repository = string
    chart      = string
    version    = string
  }))
  default = {
    karpenter = {
      repository = "oci://public.ecr.aws/karpenter"
      chart      = "karpenter"
      version    = "0.36.1"
    }
  }
}
