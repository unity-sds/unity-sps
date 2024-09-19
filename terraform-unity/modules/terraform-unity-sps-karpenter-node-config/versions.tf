terraform {
  required_version = "~> 1.8.2"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.50.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.29.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "3.2.2"
    }
  }
}
