variable "project" {
  description = "The project or mission deploying Unity SPS"
  type        = string
}

variable "venue" {
  description = "The SMCE venue in which the cluster will be deployed (dev, test, prod)"
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

variable "helm_values_template" {
  description = "The helm values template file to use."
  type        = string
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

variable "multi_git_sync_docker_image" {
  description = "Docker image for multi-git-sync container."
  type = object({
    name = string
    tag  = string
  })
}

variable "karpenter_node_pools" {
  description = "Names of the Karpenter node pools"
  type        = list(string)
}

variable "keycloak_provider_url" {
  description = "Keycloak OIDC provider URL including realm (e.g., https://keycloak.example.com/realms/MAAP)"
  type        = string
  default     = "https://dit.kc-test-maap.xyz/realms/MAAP"
}

variable "keycloak_client_id" {
  description = "Keycloak OIDC client ID for Airflow authentication"
  type        = string
  default     = "airflow"
}

variable "enable_oidc_auth" {
  description = "Enable Keycloak OIDC authentication for Airflow"
  type        = bool
  default     = true
}

variable "keycloak_role_mapping" {
  description = "Mapping of Keycloak groups to Airflow roles"
  type        = map(list(string))
  default = {
    "airflow_admin"  = ["Admin"]
    "airflow_op"     = ["Op"]
    "airflow_user"   = ["User"]
    "airflow_viewer" = ["Viewer"]
    "airflow_public" = ["Public"]
  }
}
