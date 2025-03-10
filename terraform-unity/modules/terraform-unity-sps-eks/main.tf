terraform {
  backend "s3" {
    bucket               = "unity-unity-dev-bucket"
    workspace_key_prefix = "sps/tfstates"
    key                  = "terraform.tfstate"
    region               = "us-west-2"
    encrypt              = true
  }
}

module "unity-eks" {
  source          = "git::https://github.com/unity-sds/unity-cs-infra.git//terraform-unity-eks_module?ref=unity-sps-2.4.1-hotfix1"
  deployment_name = local.cluster_name
  project         = var.project
  venue           = var.venue
  nodegroups      = var.nodegroups
  aws_auth_roles = [{
    rolearn  = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/mcp-tenantOperator"
    username = "admin"
    groups   = ["system:masters"]
  }]
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "eks")
    Component = "eks"
    Stack     = "eks"
  })
  cluster_version = "1.29"
}

resource "null_resource" "eks_post_deployment_actions" {
  depends_on = [module.unity-eks]
  provisioner "local-exec" {
    command = "${path.module}/eks_post_deployment_actions.sh ${data.aws_region.current.name} ${local.cluster_name}"
  }
}

# add extra policies as inline policy
resource "aws_iam_role_policy" "sps_airflow_eks_inline_policy" {
  name   = format(local.resource_name_prefix, "EksInlinePolicy")
  role   = module.unity-eks.cluster_iam_role
  policy = <<EOT
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Statement1",
            "Effect": "Allow",
            "Action": [
                "elasticloadbalancing:AddTags",
                "elasticloadbalancing:Describe*",
                "elasticloadbalancing:ConfigureHealthCheck",
                "elasticloadbalancing:CreateLoadBalancer",
                "elasticloadbalancing:DeleteLoadBalancer",
                "elasticloadbalancing:ModifyLoadBalancerAttributes",
                "elasticloadbalancing:RegisterTargets",
                "elasticloadbalancing:RegisterInstancesWithLoadBalancer",
                "elasticloadbalancing:DeregisterInstancesFromLoadBalancer",
                "elasticloadbalancing:DeregisterTargets",
                "ec2:AuthorizeSecurityGroupIngress",
                "ec2:AuthorizeSecurityGroupEgress",
                "ec2:CreateSecurityGroup",
                "ec2:Describe*",
                "ec2:RevokeSecurityGroupIngress"
            ],
            "Resource": "*"
        }
    ]
}
EOT
}
