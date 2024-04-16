variable "project" {
  description = "The project or mission deploying Unity SPS."
  type        = string
  default     = "unity"
}

variable "venue" {
  description = "The MCP venue in which the resources will be deployed."
  type        = string
  validation {
    condition     = can(regex("^(dev|test|prod|sbg-dev)$", var.venue))
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
  default     = "2.0.0"
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
      version    = "v2.13.2"
    }
    karpenter = {
      repository = "oci://public.ecr.aws/karpenter"
      chart      = "karpenter"
      version    = "0.36.0"
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
  })
  default = {
    airflow = {
      name = "ghcr.io/unity-sds/unity-sps/sps-airflow"
      tag  = "2.0.0"
    },
    ogc_processes_api = {
      name = "ghcr.io/unity-sds/unity-sps-ogc-processes-api/unity-sps-ogc-processes-api"
      tag  = "2.0.0"
    }
  }
}

variable "mcp_al2_eks_optimized_ami" {
  description = "The MCP Amazon Linux 2 (AL2) EKS Optimized AMI"
  type = object({
    image_id = string
    owner    = string
  })
  default = {
    image_id = "ami-0121a9a72d2b29816"
    owner    = "794625662971"
  }
}

variable "karpenter_default_node_pool_requirements" {
  description = "Requirements for the default Karpenter node pool"
  type = map(object({
    key      = string
    operator = string
    values   = list(string)
  }))
  default = {
    instance_category = {
      key      = "karpenter.k8s.aws/instance-category",
      operator = "In",
      values   = ["m", "t", "c", "r"]
    },
    instance_cpu = {
      key      = "karpenter.k8s.aws/instance-cpu",
      operator = "In",
      values   = ["2", "4", "8", "16", "32"]
    },
    instance_hypervisor = {
      key      = "karpenter.k8s.aws/instance-hypervisor",
      operator = "In",
      values   = ["nitro"]
    },
    instance_generation = {
      key      = "karpenter.k8s.aws/instance-generation",
      operator = "Gt",
      values   = ["2"]
    }
  }
}

variable "karpenter_default_node_pool_limits" {
  description = "Limits for the default Karpenter node pool"
  type = object({
    cpu = number
  })
  default = {
    cpu = 1000
  }
}

variable "karpenter_default_node_pool_disruption" {
  description = "Disruption policy for the default Karpenter node pool"
  type = object({
    consolidationPolicy = string
    consolidateAfter    = string
  })
  default = {
    consolidationPolicy = "WhenEmpty"
    consolidateAfter    = "30s"
  }
}
