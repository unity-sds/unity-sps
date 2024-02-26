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

resource "helm_release" "airflow" {
  name       = "airflow"
  repository = var.helm_charts.airflow.repository
  chart      = var.helm_charts.airflow.chart
  version    = var.helm_charts.airflow.version
  namespace  = kubernetes_namespace.airflow.metadata[0].name
  values = [
    templatefile("${path.module}/../../../airflow/helm/values.tmpl.yaml", {
      airflow_image_repo       = var.custom_airflow_docker_image.name
      airflow_image_tag        = var.custom_airflow_docker_image.tag
      kubernetes_namespace     = kubernetes_namespace.airflow.metadata[0].name
      metadata_secret_name     = "airflow-metadata-secret"
      webserver_secret_name    = "airflow-webserver-secret"
      airflow_logs_s3_location = "s3://${aws_s3_bucket.airflow_logs.id}"
      airflow_worker_role_arn  = data.aws_eks_node_group.default.node_role_arn
    })
  ]
  set_sensitive {
    name  = "webserver.defaultUser.password"
    value = var.airflow_webserver_password
  }
  depends_on = [aws_db_instance.airflow_db, helm_release.keda, kubernetes_secret.airflow_metadata, kubernetes_secret.airflow_webserver]
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
      }
    }
  }
  wait_for_load_balancer = true
  depends_on             = [helm_release.airflow]
}
