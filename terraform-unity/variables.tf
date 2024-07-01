variable "project" {
  description = "The project or mission deploying Unity SPS."
  type        = string
  default     = "unity"
}

variable "venue" {
  description = "The MCP venue in which the resources will be deployed."
  type        = string
  validation {
    condition     = can(regex("^(dev|test|prod|ops|sbg-dev)$", var.venue))
    error_message = "Invalid deployment type."
  }
}

variable "service_area" {
  description = "The service area owner of the resources being deployed."
  type        = string
  default     = "sps"
}

variable "deployment_name" {
  description = "The name of the deployment."
  type        = string
}

variable "counter" {
  description = "Identifier used to uniquely distinguish resources. This is used in the naming convention of the resource. If left empty, a random hexadecimal value will be generated and used instead."
  type        = string
  default     = ""
}

variable "release" {
  description = "The software release version."
  type        = string
  default     = "2.0.2-beta.0"
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
  default = {
    airflow = {
      repository = "https://airflow.apache.org"
      chart      = "airflow"
      version    = "1.13.1"
    },
    keda = {
      repository = "https://kedacore.github.io/charts"
      chart      = "keda"
      version    = "v2.14.2"
    }
  }
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
    git_sync = object({
      name = string
      tag  = string
    })
    redis = object({
      name = string
      tag  = string
    })
  })
  default = {
    airflow = {
      name = "ghcr.io/unity-sds/unity-sps/sps-airflow"
      tag  = "2.1.0"
    },
    ogc_processes_api = {
      name = "ghcr.io/unity-sds/unity-sps-ogc-processes-api/unity-sps-ogc-processes-api"
      tag  = "2.1.0"
    }
    git_sync = {
      name = "registry.k8s.io/git-sync/git-sync"
      tag  = "v4.2.3"
    },
    redis = {
      name = "redis"
      tag  = "7.2.4"
    }
  }
}

variable "mcp_ami_owner_id" {
  description = "The owner ID of the MCP AMIs"
  type        = string
  default     = "794625662971"
}

variable "karpenter_node_pools" {
  description = "Configuration for Karpenter node pools"
  type = map(object({
    requirements : list(object({
      key : string
      operator : string
      values : list(string)
    }))
    limits : object({
      cpu : string
      memory : string
    })
    disruption : object({
      consolidationPolicy : string
      consolidateAfter : string
    })
  }))
  default = {
    "airflow-kubernetes-pod-operator" = {
      requirements = [
        {
          key      = "karpenter.k8s.aws/instance-family"
          operator = "In"
          values   = ["m7i", "m6i", "m5", "t3", "c7i", "c6i", "c5", "r7i", "r6i", "r5"]
        },
        {
          key      = "karpenter.k8s.aws/instance-cpu"
          operator = "Gt"
          values   = ["1"] // From 2 inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-cpu"
          operator = "Lt"
          values   = ["17"] // To 16 inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-memory"
          operator = "Gt"
          values   = ["8191"] // From 8 GB inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-memory"
          operator = "Lt"
          values   = ["32769"] // To 32 GB inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-hypervisor",
          operator = "In",
          values   = ["nitro"]
        }
      ]
      limits = {
        cpu    = "100"
        memory = "400Gi"
      }
      disruption = {
        consolidationPolicy = "WhenEmpty"
        consolidateAfter    = "1m"
      }
    },
    "airflow-celery-workers" = {
      requirements = [
        {
          key      = "karpenter.k8s.aws/instance-family"
          operator = "In"
          values   = ["m7i", "m6i", "m5", "t3", "c7i", "c6i", "c5", "r7i", "r6i", "r5"]
        },
        {
          key      = "karpenter.k8s.aws/instance-cpu"
          operator = "Gt"
          values   = ["1"] // From 2 inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-cpu"
          operator = "Lt"
          values   = ["9"] // To 8 inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-memory"
          operator = "Gt"
          values   = ["8191"] // From 8 GB inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-memory"
          operator = "Lt"
          values   = ["32769"] // To 32 GB inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-hypervisor",
          operator = "In",
          values   = ["nitro"]
        }
      ]
      limits = {
        cpu    = "80"
        memory = "320Gi"
      }
      disruption = {
        consolidationPolicy = "WhenEmpty"
        consolidateAfter    = "1m"
      }
    },
    "airflow-core-components" = {
      requirements = [
        {
          key      = "karpenter.k8s.aws/instance-family"
          operator = "In"
          values   = ["m7i", "m6i", "m5", "t3", "c7i", "c6i", "c5", "r7i", "r6i", "r5"]
        },
        {
          key      = "karpenter.k8s.aws/instance-cpu"
          operator = "Gt"
          values   = ["1"] // From 2 inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-cpu"
          operator = "Lt"
          values   = ["17"] // To 16 inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-memory"
          operator = "Gt"
          values   = ["8191"] // From 8 GB inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-memory"
          operator = "Lt"
          values   = ["32769"] // To 32 GB inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-hypervisor",
          operator = "In",
          values   = ["nitro"]
        }
      ]
      limits = {
        cpu    = "40"
        memory = "160Gi"
      }
      disruption = {
        consolidationPolicy = "WhenEmpty"
        consolidateAfter    = "1m"
      }
    }
  }
}

variable "dag_catalog_repo" {
  description = "Git repository that stores the catalog of Airflow DAGs."
  type = object({
    url                 = string
    ref                 = string
    dags_directory_path = string
  })
  default = {
    url                 = "https://github.com/unity-sds/unity-sps.git"
    ref                 = "develop"
    dags_directory_path = "airflow/dags"
  }
}
