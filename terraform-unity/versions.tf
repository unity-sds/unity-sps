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
    null = {
      source  = "hashicorp/null"
      version = "3.2.2"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "5.50.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "0.11.1"
    }
  }
}
