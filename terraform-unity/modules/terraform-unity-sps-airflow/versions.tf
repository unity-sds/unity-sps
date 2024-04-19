terraform {
  required_version = "~> 1.7.2"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.25.2"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "2.12.1"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.6.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "3.2.2"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "5.43.0"
    }
    kubectl = {
      source  = "alekc/kubectl"
      version = "2.0.4"
    }
    time = {
      source  = "hashicorp/time"
      version = "0.11.1"
    }
  }
}
