terraform {
  required_version = "~> 1.8.2"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.29.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "2.13.1"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "5.47.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.6.1"
    }
  }
}
