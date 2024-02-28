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

variable "counter" {
  description = "value"
  type        = string
}

variable "release" {
  description = "The SPS release version"
  type        = string
}

variable "eks_cluster_name" {
  description = "value"
  type        = string
}

variable "kubeconfig_filepath" {
  description = "Path to the kubeconfig file for the Kubernetes cluster"
  type        = string
}

variable "airflow_webserver_password" {
  description = "value"
  type        = string
}

variable "helm_charts" {
  description = "Settings for the required Helm charts."
  type = map(object({
    repository = string
    chart      = string
    version    = string
  }))
}

variable "docker_images" {
  description = "Docker images for the services."
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
