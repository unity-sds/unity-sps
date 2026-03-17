# IAM Policy for S3 access
resource "aws_iam_policy" "ogc_processes_api_s3_policy" {
  name        = "${var.project}-${var.venue}-ogc-api-s3-policy"
  description = "Allows OGC Processes API to read DAG catalog repository configuration from S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "arn:aws:s3:::${local.dag_catalog_config_bucket}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::${local.dag_catalog_config_bucket}"
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "s3-policy")
    Component = "OGC"
    Stack     = "OGC"
  })
}

# IAM Role for IRSA (IAM Roles for Service Accounts)
resource "aws_iam_role" "ogc_processes_api_role" {
  name        = "${var.project}-${var.venue}-ogc-api-role"
  description = "IAM role for OGC Processes API pod to access AWS resources via IRSA"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${local.oidc_provider_url}"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${local.oidc_provider_url}:sub" = "system:serviceaccount:${var.kubernetes_namespace}:ogc-processes-api"
            "${local.oidc_provider_url}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  managed_policy_arns  = [aws_iam_policy.ogc_processes_api_s3_policy.arn]
  permissions_boundary = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/zsmce-tenantOperator-AMI-APIG"

  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "iam-role")
    Component = "OGC"
    Stack     = "OGC"
  })
}

# Kubernetes Service Account with IRSA annotation
resource "kubernetes_service_account" "ogc_processes_api" {
  metadata {
    name      = "ogc-processes-api"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.ogc_processes_api_role.arn
    }
  }
}

# S3 Object for repository list (bucket is managed externally)
# NOTE: This resource is commented out because the file is managed manually
# The application will still read from this S3 location via the multi-git-sync container
# resource "aws_s3_object" "dag_catalog_repos" {
#   bucket  = local.dag_catalog_config_bucket
#   key     = "dag_repos_airflow.json"
#   content = jsonencode([
#     {
#       url  = var.dag_catalog_repo.url
#       ref  = var.dag_catalog_repo.ref
#       path = var.dag_catalog_repo.dags_directory_path
#       name = "unity-sps"
#     }
#   ])
#   content_type = "application/json"
#
#   tags = merge(local.common_tags, {
#     Name      = format(local.resource_name_prefix, "dag-repos-config")
#     Component = "OGC"
#     Stack     = "OGC"
#   })
#
#   lifecycle {
#     ignore_changes = [content]
#   }
# }

resource "kubernetes_deployment" "redis" {
  metadata {
    name      = "ogc-processes-api-redis-lock"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "redis"
      }
    }
    template {
      metadata {
        labels = {
          app = "redis"
        }
      }
      spec {
        affinity {
          node_affinity {
            required_during_scheduling_ignored_during_execution {
              node_selector_term {
                match_expressions {
                  key      = "karpenter.sh/nodepool"
                  operator = "In"
                  values   = compact([for pool in var.karpenter_node_pools : pool if pool == "airflow-core-components"])
                }
                match_expressions {
                  key      = "karpenter.sh/capacity-type"
                  operator = "In"
                  values   = ["on-demand"]
                }
                match_expressions {
                  key      = "karpenter.k8s.aws/instance-family"
                  operator = "In"
                  values   = ["m5", "m6i", "t3"]
                }
                match_expressions {
                  key      = "karpenter.k8s.aws/instance-cpu"
                  operator = "In"
                  values   = ["4"]
                }
              }
            }
          }
        }
        container {
          name  = "redis"
          image = "${var.docker_images.redis.name}:${var.docker_images.redis.tag}"
          port {
            container_port = 6379
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "redis" {
  metadata {
    name      = "ogc-processes-api-redis-lock"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
  spec {
    selector = {
      app = "redis"
    }
    port {
      name        = "redis"
      port        = 6379
      target_port = 6379
    }
    type = "ClusterIP"
  }
}

resource "kubernetes_deployment" "ogc_processes_api" {
  metadata {
    name      = "ogc-processes-api"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
  spec {
    replicas = 2
    selector {
      match_labels = {
        app = "ogc-processes-api"
      }
    }
    template {
      metadata {
        labels = {
          app = "ogc-processes-api"
        }
      }
      spec {
        service_account_name = kubernetes_service_account.ogc_processes_api.metadata[0].name
        affinity {
          node_affinity {
            required_during_scheduling_ignored_during_execution {
              node_selector_term {
                match_expressions {
                  key      = "karpenter.sh/nodepool"
                  operator = "In"
                  values   = compact([for pool in var.karpenter_node_pools : pool if pool == "airflow-core-components"])
                }
                match_expressions {
                  key      = "karpenter.sh/capacity-type"
                  operator = "In"
                  values   = ["on-demand"]
                }
                match_expressions {
                  key      = "karpenter.k8s.aws/instance-family"
                  operator = "In"
                  values   = ["m5", "m6i", "t3"]
                }
                match_expressions {
                  key      = "karpenter.k8s.aws/instance-cpu"
                  operator = "In"
                  values   = ["4"]
                }
              }
            }
          }
        }
        container {
          name  = "ogc-processes-api"
          image = "${var.docker_images.ogc_processes_api.name}:${var.docker_images.ogc_processes_api.tag}"
          port {
            container_port = 80
          }
          env {
            name  = "DB_URL"
            value = "postgresql://${data.aws_db_instance.db.master_username}:${urlencode(data.aws_secretsmanager_secret_version.db.secret_string)}@${data.aws_db_instance.db.endpoint}/${data.aws_db_instance.db.db_name}"
          }
          env {
            name  = "REDIS_HOST"
            value = "${kubernetes_service.redis.metadata[0].name}.${data.kubernetes_namespace.service_area.metadata[0].name}.svc.cluster.local"

          }
          env {
            name  = "REDIS_PORT"
            value = 6379
          }
          env {
            name  = "EMS_API_URL"
            value = "http://airflow-webserver.${data.kubernetes_namespace.service_area.metadata[0].name}.svc.cluster.local:8080/api/v1"
          }
          env {
            name  = "EMS_API_AUTH_USERNAME"
            value = var.airflow_webserver_username
          }
          env {
            name  = "EMS_API_AUTH_PASSWORD"
            value = var.airflow_webserver_password
          }
          env {
            name  = "DAG_CATALOG_DIRECTORY"
            value = "/dag-catalog/current/"
          }
          env {
            name  = "DEPLOYED_DAGS_DIRECTORY"
            value = "/deployed-dags"
          }
          volume_mount {
            name       = "dag-catalog"
            mount_path = "/dag-catalog"
          }
          volume_mount {
            name       = "deployed-dags"
            mount_path = "/deployed-dags"
          }
        }
        container {
          name  = "multi-git-sync"
          image = "${var.multi_git_sync_docker_image.name}:${var.multi_git_sync_docker_image.tag}"
          env {
            name  = "S3_BUCKET"
            value = local.dag_catalog_config_bucket
          }
          env {
            name  = "S3_KEY"
            value = "dag_repos_airflow.json"
          }
          env {
            name  = "AWS_REGION"
            value = data.aws_region.current.name
          }
          env {
            name  = "SYNC_ROOT"
            value = "/dag-catalog"
          }
          env {
            name  = "POLL_INTERVAL"
            value = "60"
          }
          volume_mount {
            name       = "dag-catalog"
            mount_path = "/dag-catalog"
          }
        }
        volume {
          name = "deployed-dags"
          persistent_volume_claim {
            claim_name = data.kubernetes_persistent_volume_claim.airflow_deployed_dags.metadata[0].name
          }
        }
        volume {
          name = "dag-catalog"
          empty_dir {}
        }
      }
    }
  }
}

resource "kubernetes_service" "ogc_processes_api" {
  metadata {
    name      = "ogc-processes-api"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
  spec {
    selector = {
      app = "ogc-processes-api"
    }
    port {
      port        = 80
      target_port = 80
    }
    type = "ClusterIP"
  }
}

/* Note: re-enable this to allow access via the JPL network
resource "aws_security_group" "ogc_ingress_sg" {
  name        = "${var.project}-${var.venue}-ogc-ingress-sg"
  description = "SecurityGroup for OGC API LoadBalancer ingress"
  vpc_id      = data.aws_vpc.cluster_vpc.id
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "OgcLBSg")
    Component = "ogc"
    Stack     = "ogc"
  })
}*/

/* Note: re-enable this to allow access via the JPL network
#tfsec:ignore:AVD-AWS-0107
resource "aws_vpc_security_group_ingress_rule" "ogc_ingress_sg_jpl_rule" {
  for_each          = toset(["128.149.0.0/16", "137.78.0.0/16", "137.79.0.0/16"])
  security_group_id = aws_security_group.ogc_ingress_sg.id
  description       = "SecurityGroup ingress rule for JPL-local addresses"
  ip_protocol       = "tcp"
  from_port         = local.load_balancer_port
  to_port           = local.load_balancer_port
  cidr_ipv4         = each.key
}*/

/* Note: re-enable this to allow access via the JPL network
resource "kubernetes_ingress_v1" "ogc_processes_api_ingress" {
  metadata {
    name      = "ogc-processes-api-ingress"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
    annotations = {
      "alb.ingress.kubernetes.io/scheme"                              = "internet-facing"
      "alb.ingress.kubernetes.io/target-type"                         = "ip"
      "alb.ingress.kubernetes.io/subnets"                             = join(",", jsondecode(data.aws_ssm_parameter.subnet_ids.value)["public"])
      "alb.ingress.kubernetes.io/listen-ports"                        = "[{\"HTTPS\": ${local.load_balancer_port}}]"
      "alb.ingress.kubernetes.io/security-groups"                     = aws_security_group.ogc_ingress_sg.id
      "alb.ingress.kubernetes.io/manage-backend-security-group-rules" = "true"
      "alb.ingress.kubernetes.io/healthcheck-path"                    = "/health"
      "alb.ingress.kubernetes.io/certificate-arn"                     = data.aws_ssm_parameter.ssl_cert_arn.value
      "alb.ingress.kubernetes.io/ssl-policy"                          = "ELBSecurityPolicy-TLS13-1-2-2021-06"
    }
  }
  spec {
    ingress_class_name = "alb"
    rule {
      http {
        path {
          path      = "/"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service.ogc_processes_api.metadata[0].name
              port {
                number = 80
              }
            }
          }
        }
      }
    }
  }
  wait_for_load_balancer = true
}*/

resource "aws_security_group" "ogc_ingress_sg_internal" {
  name        = "${var.project}-${var.venue}-ogc-internal-ingress-sg"
  description = "SecurityGroup for OGC LoadBalancer internal ingress"
  vpc_id      = data.aws_vpc.cluster_vpc.id
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "OGCLBSg")
    Component = "ogc"
    Stack     = "ogc"
  })
}

#tfsec:ignore:AVD-AWS-0107
resource "aws_vpc_security_group_ingress_rule" "ogc_ingress_sg_proxy_rule" {
  count                        = length(data.aws_security_groups.venue_proxy_sg.ids) > 0 ? 1 : 0
  security_group_id            = aws_security_group.ogc_ingress_sg_internal.id
  description                  = "SecurityGroup ingress rule for venue-services proxy"
  ip_protocol                  = "tcp"
  from_port                    = local.load_balancer_port
  to_port                      = local.load_balancer_port
  referenced_security_group_id = data.aws_security_groups.venue_proxy_sg.ids[0]
}

#tfsec:ignore:AVD-AWS-0107
resource "aws_vpc_security_group_ingress_rule" "ogc_api_ingress_sg_proxy_rule" {
  security_group_id = aws_security_group.ogc_ingress_sg_internal.id
  description       = "SecurityGroup ingress rule for api-gateway (temporary)"
  ip_protocol       = "tcp"
  from_port         = local.load_balancer_port
  to_port           = local.load_balancer_port
  cidr_ipv4         = "0.0.0.0/0"
}

resource "kubernetes_service" "ogc_processes_api_ingress_internal" {
  metadata {
    name      = "ogc-processes-api-ingress-internal"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
    annotations = {
      "service.beta.kubernetes.io/aws-load-balancer-scheme"                              = "internal"
      "service.beta.kubernetes.io/aws-load-balancer-type"                                = "external"
      "service.beta.kubernetes.io/aws-load-balancer-nlb-target-type"                     = "ip"
      "service.beta.kubernetes.io/aws-load-balancer-subnets"                             = join(",", jsondecode(data.aws_ssm_parameter.subnet_ids.value)["private"])
      "service.beta.kubernetes.io/aws-load-balancer-healthcheck-path"                    = "/health"
      "service.beta.kubernetes.io/aws-load-balancer-attributes"                          = "load_balancing.cross_zone.enabled=true"
      "service.beta.kubernetes.io/aws-load-balancer-security-groups"                     = aws_security_group.ogc_ingress_sg_internal.id
      "service.beta.kubernetes.io/aws-load-balancer-manage-backend-security-group-rules" = "true"
      # the following annotation doesn't actually do anything yet because our aws-load-balancer-controller version is out of date
      "service.beta.kubernetes.io/aws-load-balancer-inbound-sg-rules-on-private-link-traffic" = "off"
      "service.beta.kubernetes.io/aws-load-balancer-additional-resource-tags" = join(",", [for key, value in merge(local.common_tags, {
        Name      = format(local.resource_name_prefix, "OgcLB")
        Component = "ogc"
        Stack     = "ogc"
      }) : "${key}=${value}"])
    }
  }
  spec {
    selector = {
      app = "ogc-processes-api"
    }
    type = "LoadBalancer"
    port {
      port        = local.load_balancer_port
      target_port = 80
    }
  }
  wait_for_load_balancer = true
  lifecycle { # this is necessary or terraform will try to recreate this every run
    ignore_changes = all
  }
  depends_on = [kubernetes_deployment.ogc_processes_api]
}

# wait_for_load_balancer = true is apparently a lie
# gotta put a discrete wait in here before triggering the vpc link
resource "time_sleep" "wait_for_ogc_lb" {
  depends_on      = [kubernetes_service.ogc_processes_api_ingress_internal]
  create_duration = "180s"
}

resource "aws_ssm_parameter" "ogc_processes_ui_url" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, "processing", "ogc_processes", "ui_url"])))
  description = "The URL of the OGC Proccesses API Docs UI."
  type        = "String"
  # Updated to use LoadBalancer instead of shared services domain
  value       = "http://${data.kubernetes_service.ogc_processes_api_ingress_internal.status[0].load_balancer[0].ingress[0].hostname}:${local.load_balancer_port}/redoc"
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "endpoints-ogc_processes_ui")
    Component = "SSM"
    Stack     = "SSM"
  })
  depends_on = [aws_ssm_parameter.unity_proxy_ogc_api]
}

resource "aws_ssm_parameter" "ogc_processes_api_url" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, "processing", "ogc_processes", "api_url"])))
  description = "The URL of the OGC Processes REST API."
  type        = "String"
  # Updated to use LoadBalancer instead of API Gateway
  value       = "http://${data.kubernetes_service.ogc_processes_api_ingress_internal.status[0].load_balancer[0].ingress[0].hostname}:${local.load_balancer_port}/"
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "endpoints-ogc_processes_api")
    Component = "SSM"
    Stack     = "SSM"
  })
  depends_on = [aws_ssm_parameter.unity_proxy_ogc_api]
}

resource "aws_ssm_parameter" "ogc_processes_api_health_check_endpoint" {
  name        = format("/%s", join("/", compact(["", "unity", var.project, var.venue, "component", "ogc-api"])))
  description = "The URL of the OGC Processes REST API."
  type        = "String"
  # Updated to use LoadBalancer instead of shared services domain
  value = jsonencode({
    "componentCategory" : "processing"
    "componentName" : "OGC API"
    "componentType" : "api"
    "description" : "A standards-compliant programming interface for Application deployment, job execution and job tracking. May be used to execute jobs in batches."
    "healthCheckUrl" : "http://${data.kubernetes_service.ogc_processes_api_ingress_internal.status[0].load_balancer[0].ingress[0].hostname}:${local.load_balancer_port}/health"
    "isPortalIntegrated" : false
    "landingPageUrl" : "http://${data.kubernetes_service.ogc_processes_api_ingress_internal.status[0].load_balancer[0].ingress[0].hostname}:${local.load_balancer_port}/"
  })
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "health-check-endpoints-ogc_processes_api")
    Component = "SSM"
    Stack     = "SSM"
  })
  lifecycle {
    ignore_changes = [value]
  }
  depends_on = [aws_ssm_parameter.unity_proxy_ogc_api]
}

resource "aws_ssm_parameter" "unity_proxy_ogc_api" {
  name        = format("/%s", join("/", compact(["unity", var.project, var.venue, "cs", "management", "proxy", "configurations", "016-sps-ogc-api"])))
  description = "The unity-proxy configuration for the Airflow OGC API."
  type        = "String"
  value       = <<-EOT

    <Location "/${var.project}/${var.venue}/ogc/">
      ProxyPassReverse "/"
    </Location>
    <LocationMatch "^/${var.project}/${var.venue}/ogc/(.*)$">
      ProxyPassMatch "http://${data.kubernetes_service.ogc_processes_api_ingress_internal.status[0].load_balancer[0].ingress[0].hostname}:${local.load_balancer_port}/$1" retry=5 disablereuse=On
      ProxyPreserveHost On
      FallbackResource /management/index.html
      AddOutputFilterByType INFLATE;SUBSTITUTE;DEFLATE text/html
      Substitute "s|\"/([^\"]*)|\"/${var.project}/${var.venue}/ogc/$1|q"
    </LocationMatch>

EOT
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "httpd-proxy-config-ogc")
    Component = "SSM"
    Stack     = "SSM"
  })
}

resource "aws_lambda_invocation" "unity_proxy_lambda_invocation" {
  count         = contains(data.aws_lambda_functions.lambda_check_all.function_names, "${var.project}-${var.venue}-httpdproxymanagement") ? 1 : 0
  function_name = "${var.project}-${var.venue}-httpdproxymanagement"
  input         = "{}"
  triggers = {
    redeployment = sha1(jsonencode([
      aws_ssm_parameter.unity_proxy_ogc_api
    ]))
  }
}
