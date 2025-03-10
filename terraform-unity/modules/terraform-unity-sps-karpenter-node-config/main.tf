resource "kubernetes_manifest" "karpenter_node_classes" {
  for_each = var.karpenter_node_classes

  manifest = {
    apiVersion = "karpenter.k8s.aws/v1"
    kind       = "EC2NodeClass"
    metadata = {
      name = each.key
    }
    spec = {
      amiFamily = "AL2"
      amiSelectorTerms = [{
        id = data.aws_ami.al2_eks_optimized.image_id
      }]
      userData = file("${path.module}/node-user-data.sh")
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
          volumeSize          = each.value.volume_size
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
  for_each = var.karpenter_node_classes

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
    node_class_name     = each.key
  }

  depends_on = [
    kubernetes_manifest.karpenter_node_pools
  ]
}

resource "kubernetes_manifest" "karpenter_node_pools" {
  for_each = var.karpenter_node_pools

  manifest = {
    apiVersion = "karpenter.sh/v1"
    kind       = "NodePool"
    metadata = {
      name = each.key
    }
    spec = {
      template = {
        spec = {
          nodeClassRef = {
            group = "karpenter.k8s.aws"
            kind  = "EC2NodeClass"
            name  = each.value.nodeClassRef
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
    kubernetes_manifest.karpenter_node_classes,
  ]
}
