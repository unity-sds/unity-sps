module "unity-eks" {
  source          = "git@github.com:unity-sds/unity-cs-infra.git//terraform-unity-eks_module?ref=8-launch-template-hop-limit"
  deployment_name = var.cluster_name

  nodegroups = var.nodegroups

  aws_auth_roles = [{
    rolearn  = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/mcp-tenantOperator"
    username = "admin"
    groups   = ["system:masters"]
  }]

  cluster_version = "1.27"
}

# add extra policies as inline policy
resource "aws_iam_role_policy" "sps_airflow_eks_inline_policy" {
  name   = "sps_airflow_eks_inline_policy"
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
