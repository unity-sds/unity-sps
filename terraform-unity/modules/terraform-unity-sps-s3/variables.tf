variable "project" {
  description = "The project or mission deploying Unity SPS"
  type        = string
}

variable "venue" {
  description = "The MCP venue in which the cluster will be deployed (dev, test, prod)"
  type        = string
}

variable "service_area" {
  description = "The service area owner of the resources being deployed"
  type        = string
}

variable "release" {
  description = "The software release version"
  type        = string
}

variable "kubernetes_namespace" {
  description = "The Kubernetes namespace of the SPS installation"
  type        = string
  default     = "sps"
}

variable "aws_region" {
  description = "The AWS region of the SPS installation"
  type        = string
  default     = "us-west-2"
}
