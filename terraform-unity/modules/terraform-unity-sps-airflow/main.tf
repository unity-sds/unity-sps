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

resource "null_resource" "remove_finalizers" {
  # https://keda.sh/docs/deploy/#uninstall
  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
      set -x
      for i in $(kubectl get scaledobjects -n ${self.triggers.airflow_namespace} -o jsonpath='{.items[*].kind}{"/"}{.items[*].metadata.name}{"\n"}'); do
          if [[ "$i" != "/" ]]; then
              kubectl patch $i -n ${self.triggers.airflow_namespace} -p '{"metadata":{"finalizers":null}}' --type=merge
          fi
      done
      for i in $(kubectl get scaledjobs -n ${self.triggers.airflow_namespace} -o jsonpath='{.items[*].kind}{"/"}{.items[*].metadata.name}{"\n"}'); do
          if [[ "$i" != "/" ]]; then
              kubectl patch $i -n ${self.triggers.airflow_namespace} -p '{"metadata":{"finalizers":null}}' --type=merge
          fi
      done
    EOT
  }
  triggers = {
    always_run        = timestamp()
    airflow_namespace = kubernetes_namespace.airflow.metadata[0].name
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

resource "kubernetes_role" "airflow_pod_creator" {
  metadata {
    name      = "airflow-pod-creator"
    namespace = kubernetes_namespace.airflow.metadata[0].name
  }

  rule {
    api_groups = [""]
    resources  = ["pods"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }

  rule {
    api_groups = [""]
    resources  = ["pods/log"]
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
}

resource "random_password" "airflow_db" {
  length           = 16
  special          = true
  override_special = "_!%^"
}

resource "aws_secretsmanager_secret" "airflow_db" {
  name                    = "${var.project}-${var.venue}-${var.service_area}-airflowdb-${local.counter}"
  recovery_window_in_days = 0
  tags = merge(local.common_tags, {
    Name      = "${var.project}-${var.venue}-${var.service_area}-airflow-${local.counter}"
    Component = "airflow"
    Stack     = "airflow"
  })
}

resource "aws_secretsmanager_secret_version" "airflow_db" {
  secret_id     = aws_secretsmanager_secret.airflow_db.id
  secret_string = random_password.airflow_db.result
}

resource "aws_db_subnet_group" "airflow_db" {
  name       = "${var.project}-${var.venue}-${var.service_area}-airflowdb-${local.counter}"
  subnet_ids = jsondecode(data.aws_ssm_parameter.subnet_ids.value)["private"]
  tags = merge(local.common_tags, {
    Name      = "${var.project}-${var.venue}-${var.service_area}-airflowdb-${local.counter}"
    Component = "airflow"
    Stack     = "airflow"
  })
}

# Security group for RDS
resource "aws_security_group" "rds_sg" {
  name        = "${var.project}-${var.venue}-${var.service_area}-RdsEc2-${local.counter}"
  description = "Security group for RDS instance to allow traffic from EKS nodes"
  vpc_id      = data.aws_eks_cluster.cluster.vpc_config[0].vpc_id
  tags = merge(local.common_tags, {
    Name      = "${var.project}-${var.venue}-${var.service_area}-airflow-${local.counter}"
    Component = "airflow"
    Stack     = "airflow"
  })
}

data "aws_security_group" "default" {
  vpc_id = data.aws_eks_cluster.cluster.vpc_config[0].vpc_id
  filter {
    name   = "tag:Name"
    values = ["${var.eks_cluster_name}-node"]
  }
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

resource "aws_db_instance" "airflow_db" {
  identifier             = "${var.project}-${var.venue}-${var.service_area}-airflowdb-${local.counter}"
  allocated_storage      = 100
  storage_type           = "gp3"
  engine                 = "postgres"
  engine_version         = "13.13"
  instance_class         = "db.m5d.large"
  db_name                = "airflow_db"
  username               = "airflow_db_user"
  password               = aws_secretsmanager_secret_version.airflow_db.secret_string
  parameter_group_name   = "default.postgres13"
  skip_final_snapshot    = true
  publicly_accessible    = false
  db_subnet_group_name   = aws_db_subnet_group.airflow_db.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  tags = merge(local.common_tags, {
    Name      = "${var.project}-${var.venue}-${var.service_area}-airflow-${local.counter}"
    Component = "airflow"
    Stack     = "airflow"
  })
}

resource "kubernetes_secret" "airflow_metadata" {
  metadata {
    name      = "airflow-metadata-secret"
    namespace = kubernetes_namespace.airflow.metadata[0].name
  }
  data = {
    kedaConnection = "postgresql://${aws_db_instance.airflow_db.username}:${urlencode(aws_secretsmanager_secret_version.airflow_db.secret_string)}@${aws_db_instance.airflow_db.endpoint}/${aws_db_instance.airflow_db.db_name}"
    connection     = "postgresql://${aws_db_instance.airflow_db.username}:${urlencode(aws_secretsmanager_secret_version.airflow_db.secret_string)}@${aws_db_instance.airflow_db.endpoint}/${aws_db_instance.airflow_db.db_name}"
  }
}

resource "aws_s3_bucket" "airflow_logs" {
  bucket        = "${var.project}-${var.venue}-${var.service_area}-airflowlogs-${local.counter}"
  force_destroy = true
  tags = merge(local.common_tags, {
    Name      = "${var.project}-${var.venue}-${var.service_area}-airflow-${local.counter}"
    Component = "airflow"
    Stack     = "airflow"
  })
}

resource "aws_iam_policy" "airflow_worker_policy" {
  name        = "${var.project}-${var.venue}-${var.service_area}-AirflowWorkerPolicy-${local.counter}"
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
            "ssm:GetParameters"
          ],
          "Resource" : "*"
        }
      ]
    }
  )
}

resource "aws_iam_role" "airflow_worker_role" {
  name = "${var.project}-${var.venue}-${var.service_area}-AirflowWorker-${local.counter}"
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

resource "aws_efs_file_system" "airflow_kpo" {
  creation_token = "${var.project}-${var.venue}-${var.service_area}-AirflowKpoEfs-${local.counter}"

  tags = merge(local.common_tags, {
    Name      = "${var.project}-${var.venue}-${var.service_area}-AirflowKpoEfs-${local.counter}"
    Component = "airflow"
    Stack     = "airflow"
  })
}

resource "aws_security_group" "airflow_kpo_efs" {
  name        = "${var.project}-${var.venue}-${var.service_area}-AirflowKpoEfsSg-${local.counter}"
  description = "Security group for the EFS used in Airflow Kubernetes Pod Operators"
  vpc_id      = data.aws_eks_cluster.cluster.vpc_config[0].vpc_id

  tags = merge(local.common_tags, {
    Name      = "${var.project}-${var.venue}-${var.service_area}-AirflowKpoEfsSg-${local.counter}"
    Component = "airflow"
    Stack     = "airflow"
  })
}

resource "aws_security_group_rule" "airflow_kpo_efs" {
  type              = "ingress"
  from_port         = 2049 # NFS port
  to_port           = 2049
  protocol          = "tcp"
  security_group_id = aws_security_group.airflow_kpo_efs.id
  cidr_blocks       = [data.aws_vpc.cluster_vpc.cidr_block] # VPC CIDR to allow entire VPC. Adjust as necessary.
}

resource "aws_efs_mount_target" "airflow_kpo" {
  for_each        = nonsensitive(toset(jsondecode(data.aws_ssm_parameter.subnet_ids.value)["private"]))
  file_system_id  = aws_efs_file_system.airflow_kpo.id
  subnet_id       = each.value
  security_groups = [aws_security_group.airflow_kpo_efs.id]
}

resource "aws_efs_access_point" "airflow_kpo" {
  file_system_id = aws_efs_file_system.airflow_kpo.id
  posix_user {
    gid = 0
    uid = 50000
  }
  root_directory {
    path = "/efs"
    creation_info {
      owner_gid   = 0
      owner_uid   = 50000
      permissions = "0755"
    }
  }
  tags = merge(local.common_tags, {
    Name      = "${var.project}-${var.venue}-${var.service_area}-AirflowKpoEfsAp-${local.counter}"
    Component = "airflow"
    Stack     = "airflow"
  })
}

resource "kubernetes_storage_class" "nfs" {
  metadata {
    name = "filestore"
  }
  reclaim_policy      = "Retain"
  storage_provisioner = "efs.csi.aws.com"
}

resource "kubernetes_persistent_volume" "efs_pv" {
  metadata {
    name = "kpo-efs"
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
        volume_handle = "${aws_efs_file_system.airflow_kpo.id}::${aws_efs_access_point.airflow_kpo.id}"
      }
    }
    storage_class_name = kubernetes_storage_class.nfs.metadata[0].name
  }
}

resource "kubernetes_persistent_volume_claim" "efs_pvc" {
  metadata {
    name      = "kpo-efs"
    namespace = kubernetes_namespace.airflow.metadata[0].name
  }
  spec {
    access_modes = ["ReadWriteMany"]
    resources {
      requests = {
        storage = "5Gi"
      }
    }
    volume_name        = "kpo-efs"
    storage_class_name = kubernetes_storage_class.nfs.metadata[0].name
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
      workers_pvc_name         = kubernetes_persistent_volume_claim.efs_pvc.metadata[0].name
    })
  ]
  set_sensitive {
    name  = "webserver.defaultUser.password"
    value = var.airflow_webserver_password
  }
  depends_on = [aws_db_instance.airflow_db, helm_release.keda, kubernetes_secret.airflow_metadata, kubernetes_secret.airflow_webserver]
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
        container {
          image = "${var.docker_images.ogc_processes_api.name}:${var.docker_images.ogc_processes_api.tag}"
          name  = "ogc-processes-api"
          port {
            container_port = 80
          }
        }
      }
    }
  }
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
