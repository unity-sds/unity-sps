#!/bin/bash
set -e

# update kube config
aws eks --region $1 update-kubeconfig --name $2
