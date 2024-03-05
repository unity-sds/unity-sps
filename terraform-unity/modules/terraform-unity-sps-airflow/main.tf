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

module "karpenter" {
  source  = "terraform-aws-modules/eks/aws//modules/karpenter"
  version = "20.5.0"

  cluster_name = data.aws_eks_cluster.cluster.name
  # rule_name_prefix
  # iam_policy_use_name_prefix

  create_node_iam_role              = false
  node_iam_role_arn                 = data.aws_eks_node_group.default_group.node_role_arn
  iam_role_permissions_boundary_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/mcp-tenantOperator-AMI-APIG"

  enable_irsa            = true
  irsa_oidc_provider_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${local.oidc_provider_url}"

  # Since the nodegroup role will already have an access entry
  create_access_entry = false

  tags = {
    Environment = "dev"
    Terraform   = "true"
  }
}

resource "helm_release" "karpenter" {
  name             = "karpenter"
  namespace        = "karpenter"
  create_namespace = true
  repository       = "oci://public.ecr.aws/karpenter"
  chart            = "karpenter"
  version          = "v0.34.0"
  wait             = false

  values = [
    <<-EOT
    settings:
      clusterName: ${data.aws_eks_cluster.cluster.name}
      clusterEndpoint: ${data.aws_eks_cluster.cluster.endpoint}
      interruptionQueue: ${module.karpenter.queue_name}
    serviceAccount:
      annotations:
        eks.amazonaws.com/role-arn: ${module.karpenter.iam_role_arn}
    EOT
  ]
}

resource "kubectl_manifest" "karpenter_node_class" {
  yaml_body = <<-YAML
    apiVersion: karpenter.k8s.aws/v1beta1
    kind: EC2NodeClass
    metadata:
      name: default
    spec:
      amiFamily: AL2
      role: ${split("/", data.aws_eks_node_group.default_group.node_role_arn)[length(split("/", data.aws_eks_node_group.default_group.node_role_arn)) - 1]}
      subnetSelectorTerms:
        - id: "${jsondecode(data.aws_ssm_parameter.subnet_ids.value)["private"][0]}"
        - id: "${jsondecode(data.aws_ssm_parameter.subnet_ids.value)["private"][1]}"
      securityGroupSelectorTerms:
        - tags:
            kubernetes.io/cluster/${data.aws_eks_cluster.cluster.name}: owned
      tags:
        karpenter.sh/discovery: ${data.aws_eks_cluster.cluster.name}
  YAML

  depends_on = [
    helm_release.karpenter
  ]
}

resource "kubectl_manifest" "karpenter_node_pool" {
  yaml_body = <<-YAML
    apiVersion: karpenter.sh/v1beta1
    kind: NodePool
    metadata:
      name: default
    spec:
      template:
        spec:
          nodeClassRef:
            name: default
          requirements:
            - key: "karpenter.k8s.aws/instance-category"
              operator: In
              values: ["c", "m", "r"]
            - key: "karpenter.k8s.aws/instance-cpu"
              operator: In
              values: ["4", "8", "16", "32"]
            - key: "karpenter.k8s.aws/instance-hypervisor"
              operator: In
              values: ["nitro"]
            - key: "karpenter.k8s.aws/instance-generation"
              operator: Gt
              values: ["2"]
      limits:
        cpu: 1000
      disruption:
        consolidationPolicy: WhenEmpty
        consolidateAfter: 30s
  YAML

  depends_on = [
    kubectl_manifest.karpenter_node_class
  ]
}

# Example deployment using the [pause image](https://www.ianlewis.org/en/almighty-pause-container)
# and starts with zero replicas
resource "kubectl_manifest" "karpenter_example_deployment" {
  yaml_body = <<-YAML
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: inflate
    spec:
      replicas: 0
      selector:
        matchLabels:
          app: inflate
      template:
        metadata:
          labels:
            app: inflate
        spec:
          terminationGracePeriodSeconds: 0
          containers:
            - name: inflate
              image: public.ecr.aws/eks-distro/kubernetes/pause:3.7
              resources:
                requests:
                  cpu: 1
  YAML

  depends_on = [
    helm_release.karpenter
  ]
}
