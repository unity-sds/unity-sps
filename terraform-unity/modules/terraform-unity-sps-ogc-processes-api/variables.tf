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

variable "kubernetes_namespace" {
  description = "The kubernetes namespace for the API's resources."
  type        = string
}

variable "db_instance_identifier" {
  description = "The AWS DB instance identifier"
  type        = string
}

variable "db_secret_arn" {
  description = "The version of the database secret in AWS Secrets Manager"
  type        = string
}

variable "airflow_deployed_dags_pvc" {
  description = "The name of the PVC for Airflow deployed DAGs"
  type        = string
}

variable "airflow_webserver_username" {
  description = "The username for the Airflow webserver and UI."
  type        = string
}

variable "airflow_webserver_password" {
  description = "The password for the Airflow webserver and UI."
  type        = string
}

variable "docker_images" {
  description = "Docker images for the associated services."
  type = object({
    ogc_processes_api = object({
      name = string
      tag  = string
    })
    git_sync = object({
      name = string
      tag  = string
    })
    redis = object({
      name = string
      tag  = string
    })
  })
}

variable "dag_catalog_repo" {
  description = "Git repository that stores the catalog of Airflow DAGs."
  type = object({
    url                 = string
    ref                 = string
    dags_directory_path = string
  })
}

variable "karpenter_node_pools" {
  description = "Names of the Karpenter node pools"
  type        = list(string)
}

variable "unity_client_id" {
  description = "Client ID for AWS Cognito deployment"
  type        = string
  default     = ""
}

variable "unity_password" {
  description = "Cognito password for AWS Cognito deployment"
  type        = string
  default     = ""
}

variable "unity_username" {
  description = "Cognito username for AWS Cognito deployment"
  type        = string
  default     = ""
}
