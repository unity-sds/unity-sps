resource "random_id" "counter" {
  byte_length = 2
}

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
    airflow_namespace   = kubernetes_namespace.airflow.metadata[0].name
  }
  depends_on = [helm_release.keda, helm_release.airflow]
}

resource "kubernetes_namespace" "airflow" {
  metadata {
    name = "airflow"
  }
}

resource "random_id" "airflow_webserver_secret" {
  byte_length = 16
}

resource "kubernetes_secret" "airflow_webserver" {
  metadata {
    name      = "airflow-webserver-secret"
    namespace = kubernetes_namespace.airflow.metadata[0].name
  }
  data = {
    "webserver-secret-key" = random_id.airflow_webserver_secret.hex
  }
}

# TODO evaluate if this role is still necessary
resource "kubernetes_role" "airflow_pod_creator" {
  metadata {
    name      = "airflow-job-launcher-and-reader-role"
    namespace = kubernetes_namespace.airflow.metadata[0].name
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
    namespace = kubernetes_namespace.airflow.metadata[0].name
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.airflow_pod_creator.metadata[0].name
  }
  subject {
    kind      = "ServiceAccount"
    name      = "airflow-worker"
    namespace = kubernetes_namespace.airflow.metadata[0].name
  }
  subject {
    kind      = "ServiceAccount"
    name      = "airflow-webserver"
    namespace = kubernetes_namespace.airflow.metadata[0].name
  }
  subject {
    kind      = "ServiceAccount"
    name      = "airflow-triggerer"
    namespace = kubernetes_namespace.airflow.metadata[0].name
  }
}


resource "random_password" "sps_db" {
  length           = 16
  special          = true
  override_special = "_!%^"
}

resource "aws_secretsmanager_secret" "sps_db" {
  name                    = format(local.resource_name_prefix, "db")
  recovery_window_in_days = 0
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "db")
    Component = "processing"
    Stack     = "processing"
  })
}

resource "aws_secretsmanager_secret_version" "sps_db" {
  secret_id     = aws_secretsmanager_secret.sps_db.id
  secret_string = random_password.sps_db.result
}

resource "aws_db_subnet_group" "sps_db" {
  name       = format(local.resource_name_prefix, "db")
  subnet_ids = jsondecode(data.aws_ssm_parameter.subnet_ids.value)["private"]
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "db")
    Component = "processing"
    Stack     = "processing"
  })
}

# Security group for RDS
resource "aws_security_group" "rds_sg" {
  name        = format(local.resource_name_prefix, "RdsEc2")
  description = "Security group for RDS instance to allow traffic from EKS nodes"
  vpc_id      = data.aws_eks_cluster.cluster.vpc_config[0].vpc_id
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "RdsEc2")
    Component = "airflow"
    Stack     = "airflow"
  })
}

# Ingress rule for RDS security group to allow PostgreSQL traffic from EKS nodes security group
resource "aws_security_group_rule" "rds_ingress_from_eks" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.rds_sg.id
  source_security_group_id = data.aws_security_group.default.id
}

# Egress rule for EKS nodes security group to allow PostgreSQL traffic to RDS security group
resource "aws_security_group_rule" "eks_egress_to_rds" {
  type                     = "egress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = data.aws_security_group.default.id
  source_security_group_id = aws_security_group.rds_sg.id
}

resource "aws_db_instance" "sps_db" {
  identifier             = format(local.resource_name_prefix, "spsdb")
  allocated_storage      = 100
  storage_type           = "gp3"
  engine                 = "postgres"
  engine_version         = "13.13"
  instance_class         = "db.m5d.large"
  db_name                = "sps_db"
  username               = "sps_db_user"
  password               = aws_secretsmanager_secret_version.sps_db.secret_string
  parameter_group_name   = "default.postgres13"
  skip_final_snapshot    = true
  publicly_accessible    = false
  db_subnet_group_name   = aws_db_subnet_group.sps_db.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "db")
    Component = "processing"
    Stack     = "processing"
  })
}

resource "kubernetes_secret" "airflow_metadata" {
  metadata {
    name      = "airflow-metadata-secret"
    namespace = kubernetes_namespace.airflow.metadata[0].name
  }
  data = {
    kedaConnection = "postgresql://${aws_db_instance.sps_db.username}:${urlencode(aws_secretsmanager_secret_version.sps_db.secret_string)}@${aws_db_instance.sps_db.endpoint}/${aws_db_instance.sps_db.db_name}"
    connection     = "postgresql://${aws_db_instance.sps_db.username}:${urlencode(aws_secretsmanager_secret_version.sps_db.secret_string)}@${aws_db_instance.sps_db.endpoint}/${aws_db_instance.sps_db.db_name}"
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
            "sqs:SendMessage",
            "sqs:ReceiveMessage",
            "sns:Publish",
            "ecr:GetDownloadUrlForLayer",
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
              "${local.oidc_provider_url}:sub" : "system:serviceaccount:${kubernetes_namespace.airflow.metadata[0].name}:airflow-worker"
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

resource "aws_efs_file_system" "airflow" {
  creation_token = format(local.resource_name_prefix, "AirflowEfs")
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "AirflowEfs")
    Component = "airflow"
    Stack     = "airflow"
  })
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
  file_system_id  = aws_efs_file_system.airflow.id
  subnet_id       = each.value
  security_groups = [aws_security_group.airflow_efs.id]
}

resource "aws_efs_access_point" "airflow_kpo" {
  file_system_id = aws_efs_file_system.airflow.id
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
  file_system_id = aws_efs_file_system.airflow.id
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
        volume_handle = "${aws_efs_file_system.airflow.id}::${aws_efs_access_point.airflow_kpo.id}"
      }
    }
    storage_class_name = kubernetes_storage_class.efs.metadata[0].name
  }
}

resource "kubernetes_persistent_volume_claim" "airflow_kpo" {
  metadata {
    name      = "airflow-kpo"
    namespace = kubernetes_namespace.airflow.metadata[0].name
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
        volume_handle = "${aws_efs_file_system.airflow.id}::${aws_efs_access_point.airflow_deployed_dags.id}"
      }
    }
    storage_class_name = kubernetes_storage_class.efs.metadata[0].name
  }
}

resource "kubernetes_persistent_volume_claim" "airflow_deployed_dags" {
  metadata {
    name      = "airflow-deployed-dags"
    namespace = kubernetes_namespace.airflow.metadata[0].name
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

resource "helm_release" "airflow" {
  name       = "airflow"
  repository = var.helm_charts.airflow.repository
  chart      = var.helm_charts.airflow.chart
  version    = var.helm_charts.airflow.version
  namespace  = kubernetes_namespace.airflow.metadata[0].name
  values = [
    templatefile("${path.module}/../../../airflow/helm/values.tmpl.yaml", {
      airflow_image_repo       = var.docker_images.airflow.name
      airflow_image_tag        = var.docker_images.airflow.tag
      kubernetes_namespace     = kubernetes_namespace.airflow.metadata[0].name
      metadata_secret_name     = "airflow-metadata-secret"
      webserver_secret_name    = "airflow-webserver-secret"
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
      unity_deployment_name    = var.deployment_name
      unity_counter            = var.counter
      unity_cluster_name       = data.aws_eks_cluster.cluster.name
    })
  ]
  set_sensitive {
    name  = "webserver.defaultUser.password"
    value = var.airflow_webserver_password
  }
  timeout = 1200
  depends_on = [
    aws_db_instance.sps_db,
    helm_release.keda,
    kubernetes_secret.airflow_metadata,
    kubernetes_secret.airflow_webserver,
    kubernetes_manifest.karpenter_node_pools,
  ]
}

resource "kubernetes_deployment" "redis" {
  metadata {
    name      = "ogc-processes-api-redis-lock"
    namespace = kubernetes_namespace.airflow.metadata[0].name
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
    namespace = kubernetes_namespace.airflow.metadata[0].name
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
    namespace = kubernetes_namespace.airflow.metadata[0].name
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
                  values   = ["airflow-core-components"]
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
            value = "postgresql://${aws_db_instance.sps_db.username}:${urlencode(aws_secretsmanager_secret_version.sps_db.secret_string)}@${aws_db_instance.sps_db.endpoint}/${aws_db_instance.sps_db.db_name}"
          }
          env {
            name  = "REDIS_HOST"
            value = "${kubernetes_service.redis.metadata[0].name}.${kubernetes_namespace.airflow.metadata[0].name}.svc.cluster.local"

          }
          env {
            name  = "REDIS_PORT"
            value = 6379
          }
          env {
            name  = "EMS_API_URL"
            value = "http://airflow-webserver.${kubernetes_namespace.airflow.metadata[0].name}.svc.cluster.local:8080/api/v1"
          }
          env {
            name  = "EMS_API_AUTH_USERNAME"
            value = local.airflow_webserver_username
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
            claim_name = kubernetes_persistent_volume_claim.airflow_deployed_dags.metadata[0].name
          }
        }
        volume {
          name = "dag-catalog"
          empty_dir {}
        }
      }
    }
  }
  depends_on = [
    kubernetes_manifest.karpenter_node_pools
  ]
}

resource "kubernetes_service" "ogc_processes_api" {
  metadata {
    name      = "ogc-processes-api"
    namespace = kubernetes_namespace.airflow.metadata[0].name
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

resource "kubernetes_ingress_v1" "airflow_ingress" {
  metadata {
    name      = "airflow-ingress"
    namespace = kubernetes_namespace.airflow.metadata[0].name
    annotations = {
      "alb.ingress.kubernetes.io/scheme"           = "internet-facing"
      "alb.ingress.kubernetes.io/target-type"      = "ip"
      "alb.ingress.kubernetes.io/subnets"          = join(",", jsondecode(data.aws_ssm_parameter.subnet_ids.value)["public"])
      "alb.ingress.kubernetes.io/listen-ports"     = "[{\"HTTP\": 5000}]"
      "alb.ingress.kubernetes.io/healthcheck-path" = "/health"
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
        # path {
        #   path      = "/ogc-processes-api"
        #   path_type = "Prefix"
        #   backend {
        #     service {
        #       name = "ogc-processes-api"
        #       port {
        #         number = 80
        #       }
        #     }
        #   }
        # }
      }
    }
  }
  wait_for_load_balancer = true
  depends_on             = [helm_release.airflow]
}

resource "kubernetes_ingress_v1" "ogc_processes_api_ingress" {
  metadata {
    name      = "ogc-processes-api-ingress"
    namespace = kubernetes_namespace.airflow.metadata[0].name
    annotations = {
      "alb.ingress.kubernetes.io/scheme"           = "internet-facing"
      "alb.ingress.kubernetes.io/target-type"      = "ip"
      "alb.ingress.kubernetes.io/subnets"          = join(",", jsondecode(data.aws_ssm_parameter.subnet_ids.value)["public"])
      "alb.ingress.kubernetes.io/listen-ports"     = "[{\"HTTP\": 5001}]"
      "alb.ingress.kubernetes.io/healthcheck-path" = "/health"
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

resource "aws_ssm_parameter" "airflow_ui_url" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, var.deployment_name, local.counter, "processing", "airflow", "ui_url"])))
  description = "The URL of the Airflow UI."
  type        = "String"
  value       = "http://${data.kubernetes_ingress_v1.airflow_ingress.status[0].load_balancer[0].ingress[0].hostname}:5000"
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "endpoints-airflow_ui")
    Component = "SSM"
    Stack     = "SSM"
  })
}

resource "aws_ssm_parameter" "airflow_api_url" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, var.deployment_name, local.counter, "processing", "airflow", "api_url"])))
  description = "The URL of the Airflow REST API."
  type        = "String"
  value       = "http://${data.kubernetes_ingress_v1.airflow_ingress.status[0].load_balancer[0].ingress[0].hostname}:5000/api/v1"
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "endpoints-airflow_api")
    Component = "SSM"
    Stack     = "SSM"
  })
}

resource "aws_ssm_parameter" "airflow_logs" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, var.deployment_name, local.counter, "processing", "airflow", "logs"])))
  description = "The name of the S3 bucket for the Airflow logs."
  type        = "String"
  value       = aws_s3_bucket.airflow_logs.id
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "S3-airflow_logs")
    Component = "SSM"
    Stack     = "SSM"
  })
}

resource "aws_ssm_parameter" "ogc_processes_ui_url" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, var.deployment_name, local.counter, "processing", "ogc_processes", "ui_url"])))
  description = "The URL of the OGC Proccesses API Docs UI."
  type        = "String"
  value       = "http://${data.kubernetes_ingress_v1.ogc_processes_api_ingress.status[0].load_balancer[0].ingress[0].hostname}:5001/redoc"
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "endpoints-ogc_processes_ui")
    Component = "SSM"
    Stack     = "SSM"
  })
}

resource "aws_ssm_parameter" "ogc_processes_api_url" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, var.deployment_name, local.counter, "processing", "ogc_processes", "api_url"])))
  description = "The URL of the OGC Processes REST API."
  type        = "String"
  value       = "http://${data.kubernetes_ingress_v1.ogc_processes_api_ingress.status[0].load_balancer[0].ingress[0].hostname}:5001"
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "endpoints-ogc_processes_api")
    Component = "SSM"
    Stack     = "SSM"
  })
}

resource "kubernetes_manifest" "karpenter_node_class" {
  manifest = {
    apiVersion = "karpenter.k8s.aws/v1beta1"
    kind       = "EC2NodeClass"
    metadata = {
      name = "default"
    }
    spec = {
      amiFamily = "AL2"
      amiSelectorTerms = [{
        id = data.aws_ami.al2_eks_optimized.image_id
      }]
      userData = <<-EOT
        #!/bin/bash
        echo "Starting pre-bootstrap configurations..."
        # Custom script to enable IP forwarding
        sudo sed -i 's/^net.ipv4.ip_forward = 0/net.ipv4.ip_forward = 1/' /etc/sysctl.conf && sudo sysctl -p |true
        echo "Pre-bootstrap configurations applied."
      EOT
      role     = data.aws_iam_role.cluster_iam_role.name
      subnetSelectorTerms = [for subnet_id in jsondecode(data.aws_ssm_parameter.subnet_ids.value)["private"] : {
        id = subnet_id
      }]
      securityGroupSelectorTerms = [{
        tags = {
          "kubernetes.io/cluster/${data.aws_eks_cluster.cluster.name}" = "owned"
          "Name"                                                       = "${data.aws_eks_cluster.cluster.name}-node"
        }
      }]
      blockDeviceMappings = [for bd in tolist(data.aws_ami.al2_eks_optimized.block_device_mappings) : {
        deviceName = bd.device_name
        ebs = {
          volumeSize          = "${bd.ebs.volume_size}Gi"
          volumeType          = bd.ebs.volume_type
          encrypted           = bd.ebs.encrypted
          deleteOnTermination = bd.ebs.delete_on_termination
        }
      }]
      metadataOptions = {
        httpEndpoint            = "enabled"
        httpPutResponseHopLimit = 3
      }
      tags = merge(local.common_tags, {
        "karpenter.sh/discovery" = data.aws_eks_cluster.cluster.name
        Name                     = format(local.resource_name_prefix, "karpenter")
        Component                = "karpenter"
        Stack                    = "karpenter"
      })
    }
  }
}

resource "kubernetes_manifest" "karpenter_node_class_high_workload" {
  manifest = {
    apiVersion = "karpenter.k8s.aws/v1beta1"
    kind       = "EC2NodeClass"
    metadata = {
      name = "airflow-kubernetes-pod-operator-high-workload"
    }
    spec = {
      amiFamily = "AL2"
      amiSelectorTerms = [{
        id = data.aws_ami.al2_eks_optimized.image_id
      }]
      userData = <<-EOT
        #!/bin/bash
        echo "Starting pre-bootstrap configurations..."
        # Custom script to enable IP forwarding
        sudo sed -i 's/^net.ipv4.ip_forward = 0/net.ipv4.ip_forward = 1/' /etc/sysctl.conf && sudo sysctl -p |true
        echo "Pre-bootstrap configurations applied."
      EOT
      role     = data.aws_iam_role.cluster_iam_role.name
      subnetSelectorTerms = [for subnet_id in jsondecode(data.aws_ssm_parameter.subnet_ids.value)["private"] : {
        id = subnet_id
      }]
      securityGroupSelectorTerms = [{
        tags = {
          "kubernetes.io/cluster/${data.aws_eks_cluster.cluster.name}" = "owned"
          "Name"                                                       = "${data.aws_eks_cluster.cluster.name}-node"
        }
      }]
      blockDeviceMappings = [for bd in tolist(data.aws_ami.al2_eks_optimized.block_device_mappings) : {
        deviceName = bd.device_name
        ebs = {
          volumeSize          = "200Gi"
          volumeType          = bd.ebs.volume_type
          encrypted           = bd.ebs.encrypted
          deleteOnTermination = bd.ebs.delete_on_termination
        }
      }]
      metadataOptions = {
        httpEndpoint            = "enabled"
        httpPutResponseHopLimit = 3
      }
      tags = merge(local.common_tags, {
        "karpenter.sh/discovery" = data.aws_eks_cluster.cluster.name
        Name                     = format(local.resource_name_prefix, "karpenter")
        Component                = "karpenter"
        Stack                    = "karpenter"
      })
    }
  }
}

resource "null_resource" "remove_node_class_finalizers" {
  # https://github.com/aws/karpenter-provider-aws/issues/5079
  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
      set -x
      export KUBECONFIG=${self.triggers.kubeconfig_filepath}
      kubectl patch ec2nodeclass ${self.triggers.node_class_name} -p '{"metadata":{"finalizers":null}}' --type=merge
    EOT
  }
  triggers = {
    kubeconfig_filepath = var.kubeconfig_filepath
    node_class_name     = kubernetes_manifest.karpenter_node_class.manifest.metadata.name
  }
  depends_on = [
    kubernetes_manifest.karpenter_node_pools
  ]
}

resource "kubernetes_manifest" "karpenter_node_pools" {
  for_each = var.karpenter_node_pools

  manifest = {
    apiVersion = "karpenter.sh/v1beta1"
    kind       = "NodePool"
    metadata = {
      name = each.key
    }
    spec = {
      template = {
        spec = {
          nodeClassRef = {
            # name = kubernetes_manifest.karpenter_node_class.manifest.metadata.name
            name = each.value.nodeClassRef
          }
          requirements = [for req in each.value.requirements : {
            key      = req.key
            operator = req.operator
            values   = req.values
          }]
        }
      }
      limits = {
        cpu    = each.value.limits.cpu
        memory = each.value.limits.memory
      }
      disruption = {
        consolidationPolicy = each.value.disruption.consolidationPolicy
        consolidateAfter    = each.value.disruption.consolidateAfter
      }
    }
  }
  depends_on = [
    kubernetes_manifest.karpenter_node_class
  ]
}


resource "null_resource" "build_lambda_packages" {
  triggers = {
    lambda_dir_sha1 = sha1(
      join("", [
        for f in fileset("${path.module}/../../../lambda/src", "**/**") : filesha1("${path.module}/../../../lambda/src/${f}")]
      )
    )
  }
  provisioner "local-exec" {
    command = <<EOF
      set -ex
      # Create a cleanup function
      cleanup() {
        # Change directory to the lambdas folder
        cd "${abspath(path.module)}/../../../lambda/src"
        for lambda_dir in */ ; do
          cd $lambda_dir

          # Run cleanup commands
          rm -rf venv
          rm -rf lambda_package
          rm -r *.egg-info || true

          # Go back to the parent directory to prepare for the next loop iteration
          cd ..
        done
      }

      # Call the cleanup function
      cleanup

      # Remove any existing built lambda packages
      rm -f "${abspath(path.module)}/../../../lambda/deployment_packages/*.zip" || true

      # Register the cleanup function to be called on exit
      trap cleanup EXIT

      # Change directory to the lambdas folder
      cd "${abspath(path.module)}/../../../lambda/src"

      # Loop over all directories in the lambdas folder../../../deployment_packages/
      for lambda_dir in */ ; do
        lambda_name=$(basename $lambda_dir)
        cd $lambda_dir

        python3.9 -m venv venv
        . venv/bin/activate
        # TODO sort out the pip version, it's causing issues with installing optional
        # dependencies in pyproject.toml. The pip version should be sorted out at
        # the Dockerfile level.
        pip install -U pip
        pip install ../../../ "unity-sps[lambda-$${lambda_name}]"
        mkdir -p lambda_package
        cp -R venv/lib/python3.9/site-packages/* ./lambda_package
        cp -R ./*.py ./lambda_package
        cd lambda_package
        zip -r $${lambda_name}_package.zip .
        mv $${lambda_name}_package.zip ../../../deployment_packages/
        deactivate
        # Go back to the parent directory (the lambdas folder) to prepare for the next loop iteration
        cd ../..
      done
    EOF
  }
}

resource "aws_s3_bucket" "inbound_staging_location" {
  bucket        = format(local.resource_name_prefix, "isl")
  force_destroy = true
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "S3-ISL")
    Component = "S3"
    Stack     = "S3"
  })
}

resource "aws_ssm_parameter" "isl_bucket" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, var.deployment_name, local.counter, "resources", "pipeline", "buckets", "isl"])))
  description = "The name of the S3 bucket for the inbound staging location."
  type        = "String"
  value       = aws_s3_bucket.inbound_staging_location.id
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "S3-isl")
    Component = "SSM"
    Stack     = "SSM"
  })
}

resource "aws_sns_topic" "s3_isl_event_topic" {
  name = format(local.resource_name_prefix, "S3IslSnsTopic")
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "SNS-S3IslSnsTopic")
    Component = "SNS"
    Stack     = "SNS"
  })
}

resource "aws_sns_topic_policy" "s3_isl_event_topic_policy" {
  arn = aws_sns_topic.s3_isl_event_topic.arn
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "s3.amazonaws.com"
      }
      Action   = "SNS:Publish"
      Resource = aws_sns_topic.s3_isl_event_topic.arn
      Condition = {
        ArnLike = {
          "aws:SourceArn" : aws_s3_bucket.inbound_staging_location.arn
        }
      }
    }]
  })
}

resource "aws_s3_bucket_notification" "isl_bucket_notification" {
  bucket = aws_s3_bucket.inbound_staging_location.id
  topic {
    topic_arn = aws_sns_topic.s3_isl_event_topic.arn
    events    = ["s3:ObjectCreated:*"]
  }
  depends_on = [
    aws_sns_topic_policy.s3_isl_event_topic_policy,
    aws_sqs_queue_policy.s3_isl_event_queue_policy
  ]
}

resource "aws_sqs_queue" "s3_isl_event_queue" {
  name                       = format(local.resource_name_prefix, "S3IslSqsQueue")
  visibility_timeout_seconds = 60
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "SQS-S3IslSqsQueue")
    Component = "SQS"
    Stack     = "SQS"
  })
}

resource "aws_sqs_queue_policy" "s3_isl_event_queue_policy" {
  queue_url = aws_sqs_queue.s3_isl_event_queue.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = "*"
        Action    = "sqs:SendMessage"
        Resource  = aws_sqs_queue.s3_isl_event_queue.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_sns_topic.s3_isl_event_topic.arn
          }
        }
      },
    ]
  })
}

resource "aws_sns_topic_subscription" "s3_isl_event_subscription" {
  topic_arn = aws_sns_topic.s3_isl_event_topic.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.s3_isl_event_queue.arn
}

resource "aws_s3_bucket" "lambdas" {
  bucket        = format(local.resource_name_prefix, "lambdas")
  force_destroy = true
  tags = merge(local.common_tags, {
    # Add or overwrite specific tags for this resource
    Name      = format(local.resource_name_prefix, "S3-lambdas")
    Component = "S3"
    Stack     = "S3"
  })
}

resource "aws_s3_object" "lambdas" {
  bucket = aws_s3_bucket.lambdas.id
  key    = format("%s.zip", format(local.resource_name_prefix, "AirflowDAGTrigger"))
  # TODO remove handcoding of lambda file name
  source     = "${abspath(path.module)}/../../../lambda/deployment_packages/airflow-dag-trigger_package.zip"
  depends_on = [null_resource.build_lambda_packages]
}

resource "aws_ssm_parameter" "airflow_dag_trigger_lambda_package" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, var.deployment_name, local.counter, "artifacts", "pipeline", "lambdas", "AirflowDAGTrigger"])))
  description = "The S3 key of the Lambda package for the Airflow Dag Trigger."
  type        = "String"
  value       = aws_s3_object.lambdas.key
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "SSM-AirflowDAGTrigger")
    Component = "SSM"
    Stack     = "SSM"
  })
}

resource "aws_iam_role" "lambda" {
  name = format(local.resource_name_prefix, "LambdaExecutionRole")
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      },
    ]
  })
  permissions_boundary = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/mcp-tenantOperator-AMI-APIG"
}

# Attach necessary policies to the role. For Lambda execution, you often need AWSLambdaBasicExecutionRole for logging etc.
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# If the Lambda interacts with specific AWS services, you might need to create and attach custom policies here.
resource "aws_iam_policy" "lambda_sqs_access" {
  name        = format(local.resource_name_prefix, "LambdaSQSAccessPolicy")
  description = "Allows Lambda function to interact with SQS queue"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ],
        Resource = aws_sqs_queue.s3_isl_event_queue.arn
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_sqs_access_attach" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.lambda_sqs_access.arn
}

resource "aws_lambda_function" "airflow_dag_trigger" {
  function_name = format(local.resource_name_prefix, "AirflowDAGTrigger")
  s3_bucket     = format(local.resource_name_prefix, "lambdas")
  s3_key        = aws_ssm_parameter.airflow_dag_trigger_lambda_package.value
  role          = aws_iam_role.lambda.arn
  handler       = "airflow_dag_trigger.lambda_handler"
  runtime       = "python3.9"
  timeout       = 60
  environment {
    variables = {
      AIRFLOW_BASE_API_ENDPOINT = aws_ssm_parameter.airflow_api_url.value
      AIRFLOW_USERNAME          = "admin"
      AIRFLOW_PASSWORD          = var.airflow_webserver_password
    }
  }
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "Lambda-AirflowDAGTrigger")
    Component = "Lambda"
    Stack     = "Lambda"
  })
  depends_on = [
    aws_cloudwatch_log_group.airflow_dag_trigger,
  ]
}

resource "aws_cloudwatch_log_group" "airflow_dag_trigger" {
  name              = "/aws/lambda/${format(local.resource_name_prefix, "AirflowDAGTrigger")}"
  retention_in_days = 14
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "CloudWatch-${format(local.resource_name_prefix, "AirflowDAGTrigger")}")
    Component = "CloudWatch"
    Stack     = "CloudWatch"
  })
}

resource "aws_lambda_event_source_mapping" "lambda_airflow_dag_trigger" {
  event_source_arn = aws_sqs_queue.s3_isl_event_queue.arn
  function_name    = aws_lambda_function.airflow_dag_trigger.arn
  batch_size       = 1
}
