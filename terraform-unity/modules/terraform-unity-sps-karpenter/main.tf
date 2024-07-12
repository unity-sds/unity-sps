# S3 backend
terraform {
  backend "s3" {
    bucket  = ""
    key     = ""
    region  = "us-west-2"
    encrypt = true
  }
}

resource "random_id" "counter" {
  byte_length = 2
}

module "karpenter" {
  source                            = "terraform-aws-modules/eks/aws//modules/karpenter"
  version                           = "20.8.5"
  cluster_name                      = local.cluster_name
  iam_policy_name                   = format(local.resource_name_prefix, "karpenter")
  iam_policy_use_name_prefix        = false
  iam_role_name                     = format(local.resource_name_prefix, "karpenter")
  iam_role_use_name_prefix          = false
  create_node_iam_role              = false
  node_iam_role_arn                 = data.aws_iam_role.cluster_iam_role.arn
  iam_role_permissions_boundary_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/mcp-tenantOperator-AMI-APIG"
  enable_irsa                       = true
  irsa_oidc_provider_arn            = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${local.oidc_provider_url}"
  # Since the nodegroup role will already have an access entry
  create_access_entry = false
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "karpenter")
    Component = "karpenter"
    Stack     = "karpenter"
  })
}

resource "helm_release" "karpenter" {
  name             = "karpenter"
  namespace        = "karpenter"
  create_namespace = true
  chart            = var.helm_charts.karpenter.chart
  repository       = var.helm_charts.karpenter.repository
  version          = var.helm_charts.karpenter.version
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
