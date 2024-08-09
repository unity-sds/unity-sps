output "karpenter_node_class_names" {
  description = "Names of the Karpenter node classes"
  value       = [for class in kubernetes_manifest.karpenter_node_classes : class.manifest.metadata.name]
}

output "karpenter_node_pools" {
  description = "Names of the Karpenter node pools"
  value       = [for pool in kubernetes_manifest.karpenter_node_pools : pool.manifest.metadata.name]
}
