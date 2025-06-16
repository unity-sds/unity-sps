resource "kubernetes_namespace" "keda" {
  metadata {
    name = "keda"
  }
}

resource "helm_release" "keda" {
  name       = "keda"
  repository = var.helm_charts.keda.repository
  chart      = var.helm_charts.keda.chart
  version    = var.helm_charts.keda.version
  namespace  = kubernetes_namespace.keda.metadata[0].name
}

resource "null_resource" "remove_keda_finalizers" {
  # https://keda.sh/docs/deploy/#uninstall
  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
      set -x
      export KUBECONFIG=${self.triggers.kubeconfig_filepath}
      for i in $(kubectl get scaledobjects -n ${self.triggers.airflow_namespace} -o jsonpath='{.items[*].metadata.name}{"\n"}'); do
          kubectl patch ScaledObject/$i -n ${self.triggers.airflow_namespace} -p '{"metadata":{"finalizers":null}}' --type=merge
      done
      for i in $(kubectl get scaledjobs -n ${self.triggers.airflow_namespace} -o jsonpath='{.items[*].metadata.name}{"\n"}'); do
          kubectl patch ScaledJob/$i -n ${self.triggers.airflow_namespace} -p '{"metadata":{"finalizers":null}}' --type=merge
      done
    EOT
  }
  triggers = {
    always_run          = timestamp()
    kubeconfig_filepath = var.kubeconfig_filepath
    airflow_namespace   = data.kubernetes_namespace.service_area.metadata[0].name
  }
  depends_on = [helm_release.keda, helm_release.airflow]
}

resource "random_id" "airflow_webserver_secret" {
  byte_length = 16
}

resource "kubernetes_secret" "airflow_webserver" {
  metadata {
    name      = local.airflow_webserver_kubernetes_secret
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
  data = {
    "webserver-secret-key" = random_id.airflow_webserver_secret.hex
  }
}

# TODO evaluate if this role is still necessary
resource "kubernetes_role" "airflow_pod_creator" {
  metadata {
    name      = "airflow-job-launcher-and-reader-role"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }

  # rule {
  #   api_groups = [""]
  #   resources  = ["pods"]
  #   verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  # }

  # rule {
  #   api_groups = [""]
  #   resources  = ["pods/log"]
  #   verbs      = ["get", "list", "watch"]
  # }

  rule {
    api_groups = ["batch"]
    resources  = ["jobs"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }

  # Adding permissions to access job status
  rule {
    api_groups = ["batch"]
    resources  = ["jobs/log", "jobs/status"]
    verbs      = ["get", "list", "watch"]
  }
  rule {
    api_groups = [""]
    resources  = ["jobs/log"]
    verbs      = ["get", "list", "watch"]
  }
}

resource "kubernetes_role_binding" "airflow_pod_creator_binding" {
  metadata {
    name      = "airflow-pod-creator-binding"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.airflow_pod_creator.metadata[0].name
  }
  subject {
    kind      = "ServiceAccount"
    name      = "airflow-worker"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
  subject {
    kind      = "ServiceAccount"
    name      = "airflow-webserver"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
  subject {
    kind      = "ServiceAccount"
    name      = "airflow-triggerer"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
}

resource "aws_s3_bucket" "airflow_logs" {
  bucket        = format(local.resource_name_prefix, "airflowlogs")
  force_destroy = true
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "airflowlogs")
    Component = "airflow"
    Stack     = "airflow"
  })
}

resource "aws_s3_bucket_policy" "airflow_logs_s3_policy" {
  bucket = aws_s3_bucket.airflow_logs.id
  policy = jsonencode(
    {
      "Id" : "ExamplePolicy",
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Sid" : "AllowSSLRequestsOnly",
          "Action" : "s3:*",
          "Effect" : "Deny",
          "Resource" : [
            format("%s%s", "arn:aws:s3:::", format(local.resource_name_prefix, "airflowlogs")),
            format("%s%s/%s", "arn:aws:s3:::", format(local.resource_name_prefix, "airflowlogs"), "*")
          ],
          "Condition" : {
            "Bool" : {
              "aws:SecureTransport" : "false"
            }
          },
          "Principal" : "*"
        }
      ]
    }
  )
}

resource "aws_iam_policy" "airflow_worker_policy" {
  name        = format(local.resource_name_prefix, "AirflowWorkerPolicy")
  description = "Policy for Airflow Workers to access AWS services"
  policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Effect" : "Allow",
          "Action" : [
            "logs:CreateLogStream",
            "logs:PutLogEvents",
            "logs:CreateLogGroup",
            "s3:ListBucket",
            "s3:GetObject",
            "s3:PutObject",
            "s3:DeleteObject",
            "sqs:SendMessage",
            "sqs:ReceiveMessage",
            "sns:Publish",
            "ecr:GetAuthorizationToken",
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchCheckLayerAvailability",
            "ecr:BatchGetImage",
            "secretsmanager:GetSecretValue",
            "ssm:GetParameters",
            "ssm:DescribeParameters",
            "ssm:GetParameter"
          ],
          "Resource" : "*"
        }
      ]
    }
  )
}

resource "aws_iam_role" "airflow_worker_role" {
  name = format(local.resource_name_prefix, "AirflowWorker")
  assume_role_policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Effect" : "Allow",
          "Principal" : {
            "Federated" : "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${local.oidc_provider_url}"
          },
          "Action" : "sts:AssumeRoleWithWebIdentity",
          "Condition" : {
            "StringEquals" : {
              "${local.oidc_provider_url}:sub" : "system:serviceaccount:${data.kubernetes_namespace.service_area.metadata[0].name}:airflow-worker"
            }
          }
        }
      ]
    }
  )
  permissions_boundary = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/mcp-tenantOperator-AMI-APIG"
}

resource "aws_iam_role_policy_attachment" "airflow_worker_policy_attachment" {
  role       = aws_iam_role.airflow_worker_role.name
  policy_arn = aws_iam_policy.airflow_worker_policy.arn
}

# https://github.com/hashicorp/terraform-provider-kubernetes/issues/864
resource "kubernetes_storage_class" "efs" {
  metadata {
    name = "filestore"
  }
  reclaim_policy      = "Retain"
  storage_provisioner = "efs.csi.aws.com"
}

resource "aws_security_group" "airflow_efs" {
  name        = format(local.resource_name_prefix, "AirflowEfsSg")
  description = "Security group for the EFS used in Airflow"
  vpc_id      = data.aws_eks_cluster.cluster.vpc_config[0].vpc_id
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "AirflowEfsSg")
    Component = "airflow"
    Stack     = "airflow"
  })
}

resource "aws_security_group_rule" "airflow_efs" {
  type              = "ingress"
  from_port         = 2049
  to_port           = 2049
  protocol          = "tcp"
  security_group_id = aws_security_group.airflow_efs.id
  cidr_blocks       = [data.aws_vpc.cluster_vpc.cidr_block] # VPC CIDR to allow entire VPC. Adjust as necessary.
}

resource "aws_efs_mount_target" "airflow" {
  for_each        = nonsensitive(toset(jsondecode(data.aws_ssm_parameter.subnet_ids.value)["private"]))
  file_system_id  = data.aws_efs_file_system.efs.id
  subnet_id       = each.value
  security_groups = [aws_security_group.airflow_efs.id]
}

resource "aws_efs_access_point" "airflow_kpo" {
  file_system_id = data.aws_efs_file_system.efs.id
  posix_user {
    gid = 0
    uid = 50000
  }
  root_directory {
    path = "/airflow-kpo"
    creation_info {
      owner_gid   = 0
      owner_uid   = 50000
      permissions = "0755"
    }
  }
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "EfsAirflowKpoAp")
    Component = "airflow"
    Stack     = "airflow"
  })
}

resource "aws_efs_access_point" "airflow_deployed_dags" {
  file_system_id = data.aws_efs_file_system.efs.id
  posix_user {
    gid = 0
    uid = 50000
  }
  root_directory {
    path = "/deployed-dags"
    creation_info {
      owner_gid   = 0
      owner_uid   = 50000
      permissions = "0755"
    }
  }
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "AirflowDeployedDagsAp")
    Component = "airflow"
    Stack     = "airflow"
  })
}

resource "time_sleep" "wait_for_efs_mount_target_dns_propagation" {
  # AWS recommends that you wait 90 seconds after creating a mount target before
  # you mount your file system. This wait lets the DNS records propagate fully
  # in the AWS Region where the file system is.
  depends_on      = [aws_efs_mount_target.airflow]
  create_duration = "120s"
}

resource "kubernetes_persistent_volume" "airflow_kpo" {
  metadata {
    name = "airflow-kpo"
  }
  spec {
    capacity = {
      storage = "5Gi"
    }
    access_modes                     = ["ReadWriteMany"]
    persistent_volume_reclaim_policy = "Retain"
    persistent_volume_source {
      csi {
        driver        = "efs.csi.aws.com"
        volume_handle = "${data.aws_efs_file_system.efs.id}::${aws_efs_access_point.airflow_kpo.id}"
      }
    }
    storage_class_name = kubernetes_storage_class.efs.metadata[0].name
  }
}

resource "kubernetes_persistent_volume_claim" "airflow_kpo" {
  metadata {
    name      = "airflow-kpo"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
  spec {
    access_modes = ["ReadWriteMany"]
    resources {
      requests = {
        storage = "5Gi"
      }
    }
    volume_name        = kubernetes_persistent_volume.airflow_kpo.metadata[0].name
    storage_class_name = kubernetes_storage_class.efs.metadata[0].name
  }
}

resource "kubernetes_persistent_volume" "airflow_deployed_dags" {
  metadata {
    name = "airflow-deployed-dags"
  }
  spec {
    capacity = {
      storage = "5Gi"
    }
    access_modes                     = ["ReadWriteMany"]
    persistent_volume_reclaim_policy = "Retain"
    persistent_volume_source {
      csi {
        driver        = "efs.csi.aws.com"
        volume_handle = "${data.aws_efs_file_system.efs.id}::${aws_efs_access_point.airflow_deployed_dags.id}"
      }
    }
    storage_class_name = kubernetes_storage_class.efs.metadata[0].name
  }
}

resource "kubernetes_persistent_volume_claim" "airflow_deployed_dags" {
  metadata {
    name      = "airflow-deployed-dags"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
  spec {
    access_modes = ["ReadWriteMany"]
    resources {
      requests = {
        storage = "5Gi"
      }
    }
    volume_name        = kubernetes_persistent_volume.airflow_deployed_dags.metadata[0].name
    storage_class_name = kubernetes_storage_class.efs.metadata[0].name
  }
}

resource "kubernetes_secret" "airflow_metadata" {
  metadata {
    name      = local.airflow_metadata_kubernetes_secret
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
  }
  data = {
    kedaConnection = "postgresql://${data.aws_db_instance.db.master_username}:${urlencode(data.aws_secretsmanager_secret_version.db.secret_string)}@${data.aws_db_instance.db.endpoint}/${data.aws_db_instance.db.db_name}"
    connection     = "postgresql://${data.aws_db_instance.db.master_username}:${urlencode(data.aws_secretsmanager_secret_version.db.secret_string)}@${data.aws_db_instance.db.endpoint}/${data.aws_db_instance.db.db_name}"
  }
}

resource "helm_release" "airflow" {
  name       = "airflow"
  repository = var.helm_charts.airflow.repository
  chart      = var.helm_charts.airflow.chart
  version    = var.helm_charts.airflow.version
  namespace  = data.kubernetes_namespace.service_area.metadata[0].name
  values = [
    templatefile("${path.module}/../../../airflow/helm/${var.helm_values_template}", {
      airflow_image_repo       = var.docker_images.airflow.name
      airflow_image_tag        = var.docker_images.airflow.tag
      kubernetes_namespace     = data.kubernetes_namespace.service_area.metadata[0].name
      metadata_secret_name     = local.airflow_metadata_kubernetes_secret
      webserver_secret_name    = local.airflow_webserver_kubernetes_secret
      airflow_logs_s3_location = "s3://${aws_s3_bucket.airflow_logs.id}"
      airflow_worker_role_arn  = aws_iam_role.airflow_worker_role.arn
      workers_pvc_name         = kubernetes_persistent_volume_claim.airflow_kpo.metadata[0].name
      dags_pvc_name            = kubernetes_persistent_volume_claim.airflow_deployed_dags.metadata[0].name
      webserver_instance_name  = format(local.resource_name_prefix, "airflow")
      webserver_navbar_color   = local.airflow_webserver_navbar_color
      service_area             = upper(var.service_area)
      service_area_version     = var.release
      unity_project            = var.project
      unity_venue              = var.venue
      unity_cluster_name       = data.aws_eks_cluster.cluster.name
      karpenter_node_pools     = join(",", var.karpenter_node_pools)
      cwl_dag_ecr_uri          = "${data.aws_caller_identity.current.account_id}.dkr.ecr.us-west-2.amazonaws.com"
      # Issue 404: DISABLE AIRRLOW AUTHENTICATION (https://github.com/unity-sds/unity-sps/issues/404)
      airflow_base_url         = "https://www.${data.aws_ssm_parameter.shared_services_domain.value}:4443/${var.project}/${var.venue}/sps/"
      webserver_config = indent(4, file("${path.module}/../../../airflow/config/webserver_config.py"))
    })
  ]
  set_sensitive {
    name  = "webserver.defaultUser.username"
    value = var.airflow_webserver_username
  }
  set_sensitive {
    name  = "webserver.defaultUser.password"
    value = var.airflow_webserver_password
  }
  timeout = 1200
  depends_on = [
    helm_release.keda,
    kubernetes_secret.airflow_metadata,
    kubernetes_secret.airflow_webserver,
  ]
}

/* Note: re-enable this to allow access via the JPL network
resource "aws_security_group" "airflow_ingress_sg" {
  name        = "${var.project}-${var.venue}-airflow-ingress-sg"
  description = "SecurityGroup for Airflow LoadBalancer ingress"
  vpc_id      = data.aws_vpc.cluster_vpc.id
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "AirflowLBSg")
    Component = "airflow"
    Stack     = "airflow"
  })
}*/

/* Note: re-enable this to allow access via the JPL network
#tfsec:ignore:AVD-AWS-0107
resource "aws_vpc_security_group_ingress_rule" "airflow_ingress_sg_jpl_rule" {
  for_each          = toset(["128.149.0.0/16", "137.78.0.0/16", "137.79.0.0/16"])
  security_group_id = aws_security_group.airflow_ingress_sg.id
  description       = "SecurityGroup ingress rule for JPL-local addresses"
  ip_protocol       = "tcp"
  from_port         = local.load_balancer_port
  to_port           = local.load_balancer_port
  cidr_ipv4         = each.key
}*/

/* Note: re-enable this to allow access via the JPL network
resource "kubernetes_ingress_v1" "airflow_ingress" {
  metadata {
    name      = "airflow-ingress"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
    annotations = {
      "alb.ingress.kubernetes.io/scheme"                              = "internet-facing"
      "alb.ingress.kubernetes.io/target-type"                         = "ip"
      "alb.ingress.kubernetes.io/subnets"                             = join(",", jsondecode(data.aws_ssm_parameter.subnet_ids.value)["public"])
      "alb.ingress.kubernetes.io/listen-ports"                        = "[{\"HTTPS\": ${local.load_balancer_port}}]"
      "alb.ingress.kubernetes.io/security-groups"                     = aws_security_group.airflow_ingress_sg.id
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
              name = "airflow-webserver"
              port {
                number = 8080
              }
            }
          }
        }
      }
    }
  }
  wait_for_load_balancer = true
  depends_on             = [helm_release.airflow]
}*/

resource "aws_security_group" "airflow_ingress_sg_internal" {
  name        = "${var.project}-${var.venue}-airflow-internal-ingress-sg"
  description = "SecurityGroup for Airflow LoadBalancer internal ingress"
  vpc_id      = data.aws_vpc.cluster_vpc.id
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "AirflowLBSg")
    Component = "airflow"
    Stack     = "airflow"
  })
}

#tfsec:ignore:AVD-AWS-0107
resource "aws_vpc_security_group_ingress_rule" "airflow_ingress_sg_proxy_rule" {
  count                        = length(data.aws_security_groups.venue_proxy_sg.ids) > 0 ? 1 : 0
  security_group_id            = aws_security_group.airflow_ingress_sg_internal.id
  description                  = "SecurityGroup ingress rule for venue-services proxy"
  ip_protocol                  = "tcp"
  from_port                    = local.load_balancer_port
  to_port                      = local.load_balancer_port
  referenced_security_group_id = data.aws_security_groups.venue_proxy_sg.ids[0]
}

#tfsec:ignore:AVD-AWS-0107
resource "aws_vpc_security_group_ingress_rule" "airflow_api_ingress_sg_proxy_rule" {
  security_group_id = aws_security_group.airflow_ingress_sg_internal.id
  description       = "SecurityGroup ingress rule for api-gateway (temporary)"
  ip_protocol       = "tcp"
  from_port         = local.load_balancer_port
  to_port           = local.load_balancer_port
  cidr_ipv4         = "0.0.0.0/0"
}

resource "kubernetes_service" "airflow_ingress_internal" {
  metadata {
    name      = "airflow-ingress-internal"
    namespace = data.kubernetes_namespace.service_area.metadata[0].name
    annotations = {
      "service.beta.kubernetes.io/aws-load-balancer-scheme"                              = "internal"
      "service.beta.kubernetes.io/aws-load-balancer-type"                                = "external"
      "service.beta.kubernetes.io/aws-load-balancer-nlb-target-type"                     = "ip"
      "service.beta.kubernetes.io/aws-load-balancer-subnets"                             = join(",", jsondecode(data.aws_ssm_parameter.subnet_ids.value)["private"])
      "service.beta.kubernetes.io/aws-load-balancer-healthcheck-path"                    = "/health"
      "service.beta.kubernetes.io/aws-load-balancer-attributes"                          = "load_balancing.cross_zone.enabled=true"
      "service.beta.kubernetes.io/aws-load-balancer-security-groups"                     = aws_security_group.airflow_ingress_sg_internal.id
      "service.beta.kubernetes.io/aws-load-balancer-manage-backend-security-group-rules" = "true"
      # the following annotation doesn't actually do anything yet because our aws-load-balancer-controller version is out of date
      "service.beta.kubernetes.io/aws-load-balancer-inbound-sg-rules-on-private-link-traffic" = "off"
      "service.beta.kubernetes.io/aws-load-balancer-additional-resource-tags" = join(",", [for key, value in merge(local.common_tags, {
        Name      = format(local.resource_name_prefix, "AirflowLB")
        Component = "airflow"
        Stack     = "airflow"
      }) : "${key}=${value}"])
    }
  }
  spec {
    selector = {
      app       = "airflow"
      component = "webserver"
    }

    type = "LoadBalancer"
    port {
      port        = local.load_balancer_port
      target_port = 8080
    }
  }
  wait_for_load_balancer = true
  lifecycle { # this is necessary or terraform will try to recreate this every run
    ignore_changes = all
  }
  depends_on = [helm_release.airflow]
}

# wait_for_load_balancer = true is apparently a lie
# gotta put a discrete wait in here before triggering the vpc link
resource "time_sleep" "wait_for_airflow_lb" {
  depends_on      = [kubernetes_service.airflow_ingress_internal]
  create_duration = "180s"
}

resource "aws_api_gateway_vpc_link" "rest_api_sps_vpc_link" {
  name        = "ogc-nlb-vpc-link-${var.project}-${var.venue}"
  description = "ogc-nlb-vpc-link-${var.project}-${var.venue}"
  target_arns = [data.aws_lb.airflow_k8s_lb.arn]
  depends_on  = [time_sleep.wait_for_airflow_lb]
}

resource "aws_api_gateway_resource" "rest_api_resource_sps_path" {
  rest_api_id = data.aws_api_gateway_rest_api.rest_api.id
  parent_id   = data.aws_api_gateway_rest_api.rest_api.root_resource_id
  path_part   = "sps"
}

resource "aws_api_gateway_resource" "rest_api_resource_airflow_api_path" {
  rest_api_id = data.aws_api_gateway_rest_api.rest_api.id
  parent_id   = aws_api_gateway_resource.rest_api_resource_sps_path.id
  path_part   = "api"
}

resource "aws_api_gateway_resource" "rest_api_resource_airflow_proxy_path" {
  rest_api_id = data.aws_api_gateway_rest_api.rest_api.id
  parent_id   = aws_api_gateway_resource.rest_api_resource_airflow_api_path.id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "rest_api_method_for_airflow_proxy_method" {
  rest_api_id        = data.aws_api_gateway_rest_api.rest_api.id
  resource_id        = aws_api_gateway_resource.rest_api_resource_airflow_proxy_path.id
  http_method        = "ANY"
  authorization      = "CUSTOM"
  authorizer_id      = data.aws_api_gateway_authorizer.unity_cs_common_authorizer.id
  request_parameters = { "method.request.path.proxy" = true }
}

resource "aws_api_gateway_integration" "rest_api_integration_for_airflow_api" {
  rest_api_id             = data.aws_api_gateway_rest_api.rest_api.id
  resource_id             = aws_api_gateway_resource.rest_api_resource_airflow_proxy_path.id
  http_method             = aws_api_gateway_method.rest_api_method_for_airflow_proxy_method.http_method
  type                    = "HTTP_PROXY"
  uri                     = format("%s://%s:%s%s", "http", data.kubernetes_service.airflow_ingress_internal.status[0].load_balancer[0].ingress[0].hostname, local.load_balancer_port, "/api/{proxy}")
  integration_http_method = "ANY"
  passthrough_behavior    = "WHEN_NO_MATCH"
  connection_type         = "VPC_LINK"
  connection_id           = aws_api_gateway_vpc_link.rest_api_sps_vpc_link.id

  # this integration includes a sneaky injected airflow auth header
  # when cognito groups are integrated with airflow this will need to be amended
  request_parameters = {
    "integration.request.path.proxy"           = "method.request.path.proxy"
    "integration.request.header.Authorization" = "'Basic ${base64encode("${var.airflow_webserver_username}:${var.airflow_webserver_password}")}'"
  }
  tls_config { # the k8s ingress backends aren't set up with TLS
    insecure_skip_verification = true
  }

  depends_on = [aws_api_gateway_vpc_link.rest_api_sps_vpc_link, aws_api_gateway_method.rest_api_method_for_airflow_proxy_method]
}

resource "aws_api_gateway_method_response" "response_200" {
  rest_api_id = data.aws_api_gateway_rest_api.rest_api.id
  resource_id = aws_api_gateway_resource.rest_api_resource_airflow_proxy_path.id
  http_method = aws_api_gateway_method.rest_api_method_for_airflow_proxy_method.http_method
  status_code = "200"

  depends_on = [aws_api_gateway_method.rest_api_method_for_airflow_proxy_method]
}

resource "time_sleep" "wait_for_gateway_integration" {
  # need to make sure both the proxy method and integration have time to settle before deploying
  depends_on      = [aws_api_gateway_integration.rest_api_integration_for_airflow_api]
  create_duration = "60s"
}

# API Gateway deployment
resource "aws_api_gateway_deployment" "airflow-api-gateway-deployment" {
  rest_api_id = data.aws_api_gateway_rest_api.rest_api.id
  stage_name  = var.venue
  # stage_name  = "default"
  depends_on = [time_sleep.wait_for_gateway_integration, aws_api_gateway_method_response.response_200]
}

resource "aws_ssm_parameter" "airflow_ui_url" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, "processing", "airflow", "ui_url"])))
  description = "The URL of the Airflow UI."
  type        = "String"
  value       = "https://www.${data.aws_ssm_parameter.shared_services_domain.value}:4443/${var.project}/${var.venue}/sps/"
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "endpoints-airflow_ui")
    Component = "SSM"
    Stack     = "SSM"
  })
  depends_on = [aws_ssm_parameter.unity_proxy_airflow_ui]
}

resource "aws_ssm_parameter" "airflow_ui_health_check_endpoint" {
  name        = format("/%s", join("/", compact(["", "unity", var.project, var.venue, "component", "airflow-ui"])))
  description = "The URL of the Airflow UI."
  type        = "String"
  value = jsonencode({
    "componentCategory" : "processing"
    "componentName" : "Airflow UI"
    "componentType" : "ui"
    "description" : "The primary GUI for the Science Processing System (SPS) to run and monitor jobs at scale."
    "healthCheckUrl" : "https://www.${data.aws_ssm_parameter.shared_services_domain.value}:4443/${var.project}/${var.venue}/sps/health"
    "landingPageUrl" : "https://www.${data.aws_ssm_parameter.shared_services_domain.value}:4443/${var.project}/${var.venue}/sps/"
  })
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "health-check-endpoints-airflow_ui")
    Component = "SSM"
    Stack     = "SSM"
  })
  lifecycle {
    ignore_changes = [value]
  }
  depends_on = [aws_ssm_parameter.unity_proxy_airflow_ui]
}

resource "aws_ssm_parameter" "airflow_api_url" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, "processing", "airflow", "api_url"])))
  description = "The URL of the Airflow REST API."
  type        = "String"
  value       = "${aws_api_gateway_deployment.airflow-api-gateway-deployment.invoke_url}/sps/api/v1"
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "endpoints-airflow_api")
    Component = "SSM"
    Stack     = "SSM"
  })
  depends_on = [aws_ssm_parameter.unity_proxy_airflow_ui]
}

resource "aws_ssm_parameter" "airflow_api_health_check_endpoint" {
  name        = format("/%s", join("/", compact(["", "unity", var.project, var.venue, "component", "airflow-api"])))
  description = "The URL of the Airflow REST API."
  type        = "String"
  value = jsonencode({
    "componentCategory" : "processing"
    "componentName" : "Airflow API"
    "componentType" : "api"
    "description" : "The direct API for the job management system underlying the SPS (Airflow). Typically the OGC Processes API should be used instead, because it will abstract out a particular job engine."
    "healthCheckUrl" : "${aws_api_gateway_deployment.airflow-api-gateway-deployment.invoke_url}/sps/api/v1/health"
    "landingPageUrl" : "${aws_api_gateway_deployment.airflow-api-gateway-deployment.invoke_url}/sps/api/v1"
  })
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "health-check-endpoints-airflow_api")
    Component = "SSM"
    Stack     = "SSM"
  })
  lifecycle {
    ignore_changes = [value]
  }
  depends_on = [aws_ssm_parameter.unity_proxy_airflow_ui]
}

resource "aws_ssm_parameter" "unity_proxy_airflow_ui" {
  name        = format("/%s", join("/", compact(["unity", var.project, var.venue, "cs", "management", "proxy", "configurations", "015-sps-airflow-ui"])))
  description = "The unity-proxy configuration for the Airflow UI."
  type        = "String"
  value       = <<-EOT

    <Location "/${var.project}/${var.venue}/sps/">
      ProxyPassReverse "/"
    </Location>
    <LocationMatch "^/${var.project}/${var.venue}/sps/(.*)$">
      ProxyPassMatch "http://${data.kubernetes_service.airflow_ingress_internal.status[0].load_balancer[0].ingress[0].hostname}:5000/${var.project}/${var.venue}/sps/$1" retry=5 disablereuse=On
      ProxyPreserveHost On
      FallbackResource /management/index.html
    </LocationMatch>

EOT
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "httpd-proxy-config-airflow")
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
      aws_ssm_parameter.unity_proxy_airflow_ui,
    ]))
  }
}

resource "aws_ssm_parameter" "airflow_logs" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, "processing", "airflow", "logs"])))
  description = "The name of the S3 bucket for the Airflow logs."
  type        = "String"
  value       = aws_s3_bucket.airflow_logs.id
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "S3-airflow_logs")
    Component = "SSM"
    Stack     = "SSM"
  })
}
