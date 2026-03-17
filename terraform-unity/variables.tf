variable "project" {
  description = "The project or mission deploying Unity SPS."
  type        = string
  default     = "unity"
}

variable "venue" {
  description = "The SMCE venue in which the resources will be deployed."
  type        = string
  validation {
    condition     = can(regex("^(dev|test|prod|ops|sbg-dev|int)$", var.venue))
    error_message = "Invalid deployment type."
  }
}

variable "service_area" {
  description = "The service area owner of the resources being deployed."
  type        = string
  default     = "sps"
}

variable "release" {
  description = "The software release version."
  type        = string
  default     = "25.3"
}

variable "kubeconfig_filepath" {
  description = "The path to the kubeconfig file for the Kubernetes cluster."
  type        = string
}

variable "airflow_webserver_username" {
  description = "The username for the Airflow webserver and UI."
  type        = string
  default     = "admin"
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
      version    = "1.15.0"
    },
    keda = {
      repository = "https://kedacore.github.io/charts"
      chart      = "keda"
      version    = "v2.15.1"
    }
  }
}

variable "helm_values_template" {
  description = "The helm values template file to use."
  type        = string
  default     = "values.tmpl.yaml"
}

variable "multi_git_sync_docker_image" {
  description = "Docker image for multi-git-sync container (shared by Airflow and OGC Processes API)."
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "jplmdps/multi-git-sync"
    tag  = "develop3"
  }
}

variable "airflow_docker_images" {
  description = "Docker images for the associated Airflow services."
  type = object({
    airflow = object({
      name = string
      tag  = string
    })
  })
  default = {
    airflow = {
      name = "ghcr.io/unity-sds/unity-sps/sps-airflow"
      tag  = "3.1.1"
    }
  }
}

variable "ogc_processes_docker_images" {
  description = "Docker images for the associated OGC Processes API services."
  type = object({
    ogc_processes_api = object({
      name = string
      tag  = string
    })
    redis = object({
      name = string
      tag  = string
    })
  })
  default = {
    ogc_processes_api = {
      name = "ghcr.io/unity-sds/unity-sps-ogc-processes-api/unity-sps-ogc-processes-api"
      tag  = "2.1.0"
    }
    redis = {
      name = "redis"
      tag  = "7.4.0"
    }
  }
}

# If we eventually have AMIs from our SMCE account, we need to get our account ID from an SSM parameter
variable "smce_ami_owner_id" {
  description = "The owner ID of the SMCE AMIs"
  type        = string
  default     = ""
}

variable "aws_ami_owner_id" {
  description = "The owner ID of the AWS EKS optimized AMIs (this is a AWS official owner ID)"
  type        = string
  default     = "602401143452"
}

variable "karpenter_node_classes" {
  description = "Configuration for karpenter_node_classes"
  type = map(object({
    volume_size = string
  }))
  default = {
    "default" = {
      volume_size = "30Gi"
    }
    "airflow-kubernetes-pod-operator-high-workload" = {
      volume_size = "300Gi"
    }
  }
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
  default = {
    "airflow-kubernetes-pod-operator-high-workload" = {
      nodeClassRef = "airflow-kubernetes-pod-operator-high-workload",
      requirements = [
        {
          key      = "karpenter.k8s.aws/instance-family"
          operator = "In"
          values   = ["m7i", "m6i", "m5", "t3", "c7i", "c6i", "c5"]
        },
        {
          key      = "karpenter.k8s.aws/instance-cpu"
          operator = "Gt"
          values   = ["0"] // From 0.5 inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-cpu"
          operator = "Lt"
          values   = ["65"] // To 64 inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-memory"
          operator = "Gt"
          values   = ["511"] // 0.5 GiB = 512 MiB
        },
        {
          key      = "karpenter.k8s.aws/instance-memory"
          operator = "Lt"
          # values   = ["131073"] // 128 GiB = 131072 MiB
          values = ["262145"] // 256 GiB = 262144 MiB
        },
        {
          key      = "karpenter.k8s.aws/instance-hypervisor",
          operator = "In",
          values   = ["nitro"]
        }
      ]
      limits = {
        cpu    = "6400"    # 64 CPU X 100
        memory = "12800Gi" # 128 Gi X 100
      }
      disruption = {
        consolidationPolicy = "WhenEmpty"
        consolidateAfter    = "1m"
      }
    },
    "airflow-kubernetes-pod-operator" = {
      nodeClassRef = "default",
      requirements = [
        {
          key      = "karpenter.k8s.aws/instance-family"
          operator = "In"
          values   = ["m7i", "m6i", "m5", "t3", "c7i", "c6i", "c5"]
        },
        {
          key      = "karpenter.k8s.aws/instance-cpu"
          operator = "Gt"
          values   = ["0"] // From 0.5 inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-cpu"
          operator = "Lt"
          values   = ["17"] // To 16 inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-memory"
          operator = "Gt"
          # values   = ["4095"] // 4 GiB = 4096 MiB
          values = ["511"] // 0.5 GiB = 512 MiB
        },
        {
          key      = "karpenter.k8s.aws/instance-memory"
          operator = "Lt"
          values   = ["65537"] // 64 GiB = 65536 MiB
        },
        {
          key      = "karpenter.k8s.aws/instance-hypervisor",
          operator = "In",
          values   = ["nitro"]
        }
      ]
      limits = {
        cpu    = "6400"    # 64 CPU X 100
        memory = "12800Gi" # 128 Gi X 100
      }
      disruption = {
        consolidationPolicy = "WhenEmpty"
        consolidateAfter    = "1m"
      }
    },
    "airflow-celery-workers" = {
      nodeClassRef = "default",
      requirements = [
        {
          key      = "karpenter.k8s.aws/instance-family"
          operator = "In"
          values   = ["m7i", "m6i", "m5", "t3", "c7i", "c6i", "c5"]
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
          values   = ["4095"] // From 4 GB inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-memory"
          operator = "Lt"
          values   = ["65537"] // To 64 GB inclusive
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
        consolidationPolicy = "WhenEmptyOrUnderutilized"
        consolidateAfter    = "1m"
      }
    },
    "airflow-core-components" = {
      nodeClassRef = "default",
      requirements = [
        {
          key      = "karpenter.k8s.aws/instance-family"
          operator = "In"
          values   = ["m7i", "m6i", "m5", "t3", "c7i", "c6i", "c5"]
        },
        {
          key      = "karpenter.k8s.aws/instance-cpu"
          operator = "Gt"
          values   = ["1"] // From 2 inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-cpu"
          operator = "Lt"
          values   = ["5"] // To 4 inclusive (m5.xlarge max)
        },
        {
          key      = "karpenter.k8s.aws/instance-memory"
          operator = "Gt"
          values   = ["4095"] // From 4 GB inclusive
        },
        {
          key      = "karpenter.k8s.aws/instance-memory"
          operator = "Lt"
          values   = ["16385"] // To 16 GB inclusive (m5.xlarge max)
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
    ref                 = "main"
    dags_directory_path = "airflow/dags"
  }
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

variable "db_instance_class" {
  description = "The SPS RDS database instance class"
  type        = string
  default     = "db.t3.medium"
}
