# S3 backend
terraform {
  backend "s3" {
    # full path to Terraform state file:
    # s3://<bucket>/<key>
    bucket  = ""
    key     = ""
    region  = "us-west-2"
    encrypt = true
  }
}

resource "random_id" "counter" {
  byte_length = 2
}

module "unity-eks" {

  source          = "git@github.com:unity-sds/unity-cs-infra.git//terraform-unity-eks_module?ref=unity-sps-2.1.0"
  deployment_name = local.cluster_name
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
