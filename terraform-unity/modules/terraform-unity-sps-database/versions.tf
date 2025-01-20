terraform {
  required_version = "~> 1.8.2"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "5.67.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.32.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.6.1"
    }
    external = {
      source  = "hashicorp/external"
      version = "2.3.4"
    }
  }
}
