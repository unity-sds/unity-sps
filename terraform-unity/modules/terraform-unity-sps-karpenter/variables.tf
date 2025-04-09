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
  default     = "25.1"
}

# tflint-ignore: terraform_unused_declarations
variable "deployment_name" {
  description = "The name of the deployment."
  type        = string
  default     = ""
}

# tflint-ignore: terraform_unused_declarations
variable "tags" {
  description = "Tags for the deployment (unused)"
  type        = map(string)
  default     = { empty = "" }
}

# tflint-ignore: terraform_unused_declarations
variable "installprefix" {
  description = "The install prefix for the service area (unused)"
  type        = string
  default     = ""
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
      version    = "1.0.2"
    }
  }
}
