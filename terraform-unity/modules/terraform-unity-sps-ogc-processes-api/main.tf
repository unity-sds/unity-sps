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
                  values   = ["c6i", "c5"]
                }
                match_expressions {
                  key      = "karpenter.k8s.aws/instance-cpu"
                  operator = "In"
                  values   = ["2", "4"]
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
            value = "/dag-catalog/current/${var.dag_catalog_repo.dags_directory_path}"
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
          name  = "git-sync"
          image = "${var.docker_images.git_sync.name}:${var.docker_images.git_sync.tag}"
          env {
            name  = "GITSYNC_REPO"
            value = var.dag_catalog_repo.url
          }
          env {
            name  = "GITSYNC_REF"
            value = var.dag_catalog_repo.ref
          }
          env {
            name  = "GITSYNC_ROOT"
            value = "/dag-catalog"
          }
          env {
            name  = "GITSYNC_LINK"
            value = "current"
          }
          env {
            name  = "GITSYNC_PERIOD"
            value = "3s"
          }
          env {
            name  = "GITSYNC_ONE_TIME"
            value = "false"
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

resource "aws_security_group" "ogc_ingress_sg" {
  name        = "${var.project}-${var.venue}-ogc-ingress-sg"
  description = "SecurityGroup for OGC API LoadBalancer ingress"
  vpc_id      = data.aws_vpc.cluster_vpc.id
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "OgcLBSg")
    Component = "ogc"
    Stack     = "ogc"
  })
}

resource "aws_security_group" "ogc_ingress_sg_internal" {
  name        = "${var.project}-${var.venue}-ogc-internal-ingress-sg"
  description = "SecurityGroup for OGC API LoadBalancer internal ingress"
  vpc_id      = data.aws_vpc.cluster_vpc.id
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "OgcLBSg")
    Component = "ogc"
    Stack     = "ogc"
  })
}

#tfsec:ignore:AVD-AWS-0107
resource "aws_vpc_security_group_ingress_rule" "ogc_ingress_sg_jpl_rule" {
  for_each          = toset(["128.149.0.0/16", "137.78.0.0/16", "137.79.0.0/16"])
  security_group_id = aws_security_group.ogc_ingress_sg.id
  description       = "SecurityGroup ingress rule for JPL-local addresses"
  ip_protocol       = "tcp"
  from_port         = local.load_balancer_port
  to_port           = local.load_balancer_port
  cidr_ipv4         = each.key
}

data "aws_security_groups" "venue_proxy_sg" {
  filter {
    name   = "group-name"
    values = ["${var.project}-${var.venue}-ecs_service_sg"]
  }
  tags = {
    Service = "U-CS"
  }
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
}

resource "kubernetes_ingress_v1" "ogc_processes_api_ingress_internal" {
  metadata {
    name      = "ogc-processes-api-ingress-internal"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
    annotations = {
      "alb.ingress.kubernetes.io/scheme"                              = "internal"
      "alb.ingress.kubernetes.io/target-type"                         = "ip"
      "alb.ingress.kubernetes.io/subnets"                             = join(",", jsondecode(data.aws_ssm_parameter.subnet_ids.value)["private"])
      "alb.ingress.kubernetes.io/listen-ports"                        = "[{\"HTTPS\": ${local.load_balancer_port}}]"
      "alb.ingress.kubernetes.io/security-groups"                     = aws_security_group.ogc_ingress_sg_internal.id
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
}

resource "aws_ssm_parameter" "ogc_processes_ui_url" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, "processing", "ogc_processes", "ui_url"])))
  description = "The URL of the OGC Proccesses API Docs UI."
  type        = "String"
  value       = "https://${data.kubernetes_ingress_v1.ogc_processes_api_ingress.status[0].load_balancer[0].ingress[0].hostname}:5001/redoc"
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "endpoints-ogc_processes_ui")
    Component = "SSM"
    Stack     = "SSM"
  })
}

resource "aws_ssm_parameter" "ogc_processes_api_url" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, "processing", "ogc_processes", "api_url"])))
  description = "The URL of the OGC Processes REST API."
  type        = "String"
  value       = "https://${data.kubernetes_ingress_v1.ogc_processes_api_ingress.status[0].load_balancer[0].ingress[0].hostname}:5001"
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "endpoints-ogc_processes_api")
    Component = "SSM"
    Stack     = "SSM"
  })
}

resource "aws_ssm_parameter" "ogc_processes_api_health_check_endpoint" {
  name        = format("/%s", join("/", compact(["", "unity", var.project, var.venue, "component", "ogc-api"])))
  description = "The URL of the OGC Processes REST API."
  type        = "String"
  value = jsonencode({
    "componentName" : "OGC API"
    "healthCheckUrl" : "https://${data.kubernetes_ingress_v1.ogc_processes_api_ingress_internal.status[0].load_balancer[0].ingress[0].hostname}:5001/health"
    "landingPageUrl" : "https://${data.kubernetes_ingress_v1.ogc_processes_api_ingress_internal.status[0].load_balancer[0].ingress[0].hostname}:5001"
  })
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "health-check-endpoints-ogc_processes_api")
    Component = "SSM"
    Stack     = "SSM"
  })
  lifecycle {
    ignore_changes = [value]
  }
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
      ProxyPassMatch "http://${data.kubernetes_ingress_v1.ogc_processes_api_ingress_internal.status[0].load_balancer[0].ingress[0].hostname}:5001/$1"
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

data "aws_lambda_functions" "lambda_check_all" {}

resource "aws_lambda_invocation" "unity_proxy_lambda_invocation" {
  count         = contains(data.aws_lambda_functions.lambda_check_all.function_names, "unity-${var.venue}-httpdproxymanagement") ? 1 : 0
  function_name = "unity-${var.venue}-httpdproxymanagement"
  input         = "{}"
  triggers = {
    redeployment = sha1(jsonencode([
      aws_ssm_parameter.unity_proxy_ogc_api
    ]))
  }
}
