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
  description = "The kubernetes namespace for Airflow resources."
  type        = string
}

variable "kubeconfig_filepath" {
  description = "The path to the kubeconfig file for the Kubernetes cluster."
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

variable "efs_file_system_id" {
  description = "The EFS file system ID"
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
    })
  })
}

variable "karpenter_node_pools" {
  description = "Names of the Karpenter node pools"
  type        = list(string)
}

variable "unity_cs_lambda_authorizer_function_name" {
  type        = string
  description = "Function name of the CS Lambda Authorizer"
  default     = "unity-cs-common-lambda-authorizer"
}

variable "unity_cs_lambda_authorizer_zip_path" {
  type        = string
  description = "The URL of the CS Lambda Authorizer deployment ZIP file"
  default     = "https://github.com/unity-sds/unity-cs-auth-lambda/releases/download/1.0.4/unity-cs-lambda-auth-1.0.4.zip"
}