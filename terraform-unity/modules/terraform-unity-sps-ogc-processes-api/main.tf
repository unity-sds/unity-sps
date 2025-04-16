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

resource "aws_api_gateway_vpc_link" "rest_api_ogc_vpc_link" {
  name        = "sps-nlb-vpc-link-${var.project}-${var.venue}"
  description = "sps-nlb-vpc-link-${var.project}-${var.venue}"
  target_arns = [data.aws_lb.ogc_k8s_lb.arn]
  depends_on  = [time_sleep.wait_for_ogc_lb]
}

resource "aws_api_gateway_resource" "rest_api_resource_management_path" {
  rest_api_id = data.aws_api_gateway_rest_api.rest_api.id
  parent_id   = data.aws_api_gateway_rest_api.rest_api.root_resource_id
  path_part   = "ogc"
}

resource "aws_api_gateway_resource" "rest_api_resource_ogc_api_path" {
  rest_api_id = data.aws_api_gateway_rest_api.rest_api.id
  parent_id   = aws_api_gateway_resource.rest_api_resource_management_path.id
  path_part   = "api"
}

resource "aws_api_gateway_resource" "rest_api_resource_ogc_proxy_path" {
  rest_api_id = data.aws_api_gateway_rest_api.rest_api.id
  parent_id   = aws_api_gateway_resource.rest_api_resource_ogc_api_path.id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "rest_api_method_for_ogc_proxy_method" {
  rest_api_id        = data.aws_api_gateway_rest_api.rest_api.id
  resource_id        = aws_api_gateway_resource.rest_api_resource_ogc_proxy_path.id
  http_method        = "ANY"
  authorization      = "CUSTOM"
  authorizer_id      = data.aws_api_gateway_authorizer.unity_cs_common_authorizer.id
  request_parameters = { "method.request.path.proxy" = true }
}

resource "aws_api_gateway_integration" "rest_api_integration_for_ogc_api" {
  rest_api_id             = data.aws_api_gateway_rest_api.rest_api.id
  resource_id             = aws_api_gateway_resource.rest_api_resource_ogc_proxy_path.id
  http_method             = aws_api_gateway_method.rest_api_method_for_ogc_proxy_method.http_method
  type                    = "HTTP_PROXY"
  uri                     = format("%s://%s:%s%s", "http", data.kubernetes_service.ogc_processes_api_ingress_internal.status[0].load_balancer[0].ingress[0].hostname, local.load_balancer_port, "/{proxy}")
  integration_http_method = "ANY"
  passthrough_behavior    = "WHEN_NO_MATCH"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.rest_api_ogc_vpc_link.id

  request_parameters = {
    "integration.request.path.proxy" = "method.request.path.proxy"
  }
  tls_config { # the k8s ingress backends aren't set up with TLS
    insecure_skip_verification = true
  }

  depends_on = [aws_api_gateway_vpc_link.rest_api_ogc_vpc_link, aws_api_gateway_method.rest_api_method_for_ogc_proxy_method]
}

resource "aws_api_gateway_method_response" "response_200" {
  rest_api_id = data.aws_api_gateway_rest_api.rest_api.id
  resource_id = aws_api_gateway_resource.rest_api_resource_ogc_proxy_path.id
  http_method = aws_api_gateway_method.rest_api_method_for_ogc_proxy_method.http_method
  status_code = "200"

  depends_on = [aws_api_gateway_method.rest_api_method_for_ogc_proxy_method]
}

resource "time_sleep" "wait_for_gateway_integration" {
  # need to make sure both the proxy method and integration have time to settle before deploying
  depends_on      = [aws_api_gateway_integration.rest_api_integration_for_ogc_api, aws_api_gateway_method.rest_api_method_for_ogc_proxy_method]
  create_duration = "180s"
}

# API Gateway deployment
resource "aws_api_gateway_deployment" "ogc-api-gateway-deployment" {
  rest_api_id = data.aws_api_gateway_rest_api.rest_api.id
  stage_name  = var.venue
  depends_on  = [time_sleep.wait_for_gateway_integration, aws_api_gateway_method_response.response_200]
}

resource "aws_ssm_parameter" "ogc_processes_ui_url" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, "processing", "ogc_processes", "ui_url"])))
  description = "The URL of the OGC Proccesses API Docs UI."
  type        = "String"
  value       = "https://www.${data.aws_ssm_parameter.shared_services_domain.value}:4443/${var.project}/${var.venue}/ogc/redoc"
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
  value       = "${aws_api_gateway_deployment.ogc-api-gateway-deployment.invoke_url}/ogc/api/"
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
  value = jsonencode({
    "componentName" : "OGC API"
    "healthCheckUrl" : "https://www.${data.aws_ssm_parameter.shared_services_domain.value}:4443/${var.project}/${var.venue}/ogc/health"
    "landingPageUrl" : "https://www.${data.aws_ssm_parameter.shared_services_domain.value}:4443/${var.project}/${var.venue}/ogc/"
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
