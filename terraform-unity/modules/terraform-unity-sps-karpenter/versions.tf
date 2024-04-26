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
    aws = {
      source  = "hashicorp/aws"
      version = "5.43.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.6.0"
    }
  }
}
