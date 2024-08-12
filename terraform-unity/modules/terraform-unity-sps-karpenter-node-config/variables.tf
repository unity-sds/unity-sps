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
  description = "The software release version."
  type        = string
}

variable "kubeconfig_filepath" {
  description = "The path to the kubeconfig file for the Kubernetes cluster."
  type        = string
}

variable "mcp_ami_owner_id" {
  description = "The ID of the MCP AMIs"
  type        = string
}

variable "karpenter_node_classes" {
  type = map(object({
    volume_size = string
  }))
}

variable "karpenter_node_pools" {
  description = "Configuration for Karpenter node pools"
  type = map(object({
    requirements : list(object({
      key : string
      operator : string
      values : list(string)
    }))
    nodeClassRef : string
    limits : object({
      cpu : string
      memory : string
    })
    disruption : object({
      consolidationPolicy : string
      consolidateAfter : string
    })
  }))
}
