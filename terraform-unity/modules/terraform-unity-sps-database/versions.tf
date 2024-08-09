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
    random = {
      source  = "hashicorp/random"
      version = "3.6.1"
    }
  }
}
