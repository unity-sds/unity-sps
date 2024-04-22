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

variable "deployment_name" {
  description = "The name of the deployment."
  type        = string
}

variable "counter" {
  description = "Identifier used to uniquely distinguish resources. This is used in the naming convention of the resource. If left empty, a random hexadecimal value will be generated and used instead."
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

variable "airflow_webserver_password" {
  description = "The password for the Airflow webserver and UI."
  type        = string
}

variable "helm_charts" {
  description = "Helm charts for the associated services."
  type = map(object({
    repository = string
    chart      = string
    version    = string
  }))
}

variable "docker_images" {
  description = "Docker images for the associated services."
  type = object({
    airflow = object({
      name = string
      tag  = string
    }),
    ogc_processes_api = object({
      name = string
      tag  = string
    })
  })
}

variable "mcp_ami_owner_id" {
  description = "The ID of the MCP AMIs"
  type        = string
}

variable "karpenter_default_node_pool_requirements" {
  description = "Requirements for the default Karpenter node pool"
  type = map(object({
    key      = string
    operator = string
    values   = list(string)
  }))
}

variable "karpenter_default_node_pool_limits" {
  description = "Limits for the default Karpenter node pool"
  type = object({
    cpu    = number
    memory = string
  })
}

variable "karpenter_default_node_pool_disruption" {
  description = "Disruption policy for the default Karpenter node pool"
  type = object({
    consolidationPolicy = string
    consolidateAfter    = string
  })
}

variable "karpenter_default_node_class_metadata_options" {
  description = "Disruption policy for the default Karpenter node pool"
  type = object({
    httpEndpoint            = string
    httpPutResponseHopLimit = number
  })
}
