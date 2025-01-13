#!/bin/bash
set -e

# update kube config
aws eks --region $1 update-kubeconfig --name $2

# uncomment if pods are running in a private subnet and need to communicate outbound to the internet
#kubectl set env daemonset -n kube-system aws-node AWS_VPC_K8S_CNI_EXTERNALSNAT=true

# uncomment to deploy EBS CSI driver via kustomize
#kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=release-1.36"
