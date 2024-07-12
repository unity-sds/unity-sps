#!/bin/bash
set -ex
# Script to deploy or destroy the Unity EKS, Karpenter of Airflow
#
# Syntax: ./unity_sps_deploy_or_destroy_sps.sh deploy|destroy eks|karpenter|airflow
#
# Pre-requisites:
# o Customize all parameters in the header section to target your desired deployment
# o Renew the proper AWS credentials
#
# Note:
# Components must be deployed in this order:
# deploy eks > karpenter > airflow
# Components must be destroyed in the revers order:
# destroy airflow > karpenter > eks

# Note: the first time you run "deploy" on eks/karpenter/airflow, you don't already have the $TFVARS_FILENAME
# in the proper directory, the script will stop because it cannot parse the file that was automatically generated.
# Edit that file: remove the first and last line, and add the specific values for your deployment.
# Then run the script again.

# Note:
# Must make sure we don't check in a new version of this script with a real AWS account number

# =============== START HEADER: customize this section =================

# set venue dependent AWS profile
export AWS_PROFILE=XXXXXXXXXXXX_mcp-tenantOperator
export AWS_REGION=us-west-2

# set cluster parameters
export PROJECT=unity
export SERVICE_AREA=sps
export VENUE=dev
export DEPLOYMENT=luca
export COUNTER=7
export TF_BACKEND_BUCKET=unity-unity-dev-bucket

# the root directory of the "unity-sps" installation
export UNITY_SPS_DIR=/Users/cinquini/PycharmProjects/unity-sps

# ============= END HEADER: do not change what follows ====================

# "deploy" or "destroy"
ACTION=$1

# "eks" or "karpenter" or "airflow"
COMPONENT=$2

export CLUSTER_NAME=unity-${VENUE}-sps-eks-${DEPLOYMENT}-${COUNTER}
export KUBECONFIG=${UNITY_SPS_DIR}/terraform-unity/modules/terraform-unity-sps-eks/$CLUSTER_NAME.cfg

if [ "$COMPONENT" = "eks" ]; then
   tf_dir=${UNITY_SPS_DIR}/terraform-unity/modules/terraform-unity-sps-eks
elif [ "$COMPONENT" = "karpenter" ]; then
   tf_dir=${UNITY_SPS_DIR}/terraform-unity/modules/terraform-unity-sps-karpenter
elif [ "$COMPONENT" = "airflow" ]; then
   tf_dir=${UNITY_SPS_DIR}/terraform-unity
fi
export TFVARS_FILENAME=unity-${VENUE}-sps-${COMPONENT}-${DEPLOYMENT}-${COUNTER}.tfvars

# initialize Terraform
cd $tf_dir
tfswitch 1.8.2
export TF_WORKSPACE_KEY_PREFIX="sps/tfstates"
export TF_BACKEND_KEY="terraform.tfstate"
terraform init -reconfigure -backend-config="bucket=$TF_BACKEND_BUCKET" -backend-config="workspace_key_prefix=$TF_WORKSPACE_KEY_PREFIX" -backend-config="key=$TF_BACKEND_KEY"
terraform get -update

# if new cluster --> create new tfvars file
mkdir -p tfvars
if ! [ -f tfvars/${TFVARS_FILENAME} ]; then
  terraform-docs tfvars hcl . --output-file "tfvars/${TFVARS_FILENAME}"
fi

# switch between DEPLOYMENTs
if [ "$COMPONENT" = "eks" ]; then
    if [ "$ACTION" = "deploy" ]; then
       echo "Deploying $COMPONENT"
       terraform apply --auto-approve --var-file=tfvars/$TFVARS_FILENAME
       aws eks update-kubeconfig --region us-west-2 --name $CLUSTER_NAME --kubeconfig ${KUBECONFIG}
       kubectl get all -A
    elif [ "$ACTION" = "destroy" ]; then
       echo "Destroying $COMPONENT"
       terraform destroy --auto-approve --var-file=tfvars/$TFVARS_FILENAME
    fi
elif [ "$COMPONENT" = "airflow" ]; then
    if [ "$ACTION" = "deploy" ]; then
       echo "Deploying $COMPONENT"
       terraform apply --auto-approve --var-file=tfvars/$TFVARS_FILENAME
       kubectl get all -n airflow
    elif [ "$ACTION" = "destroy" ]; then
       echo "Destroying $COMPONENT"
       terraform destroy --auto-approve --var-file=tfvars/$TFVARS_FILENAME
    fi
elif [ "$COMPONENT" = "karpenter" ]; then
    if [ "$ACTION" = "deploy" ]; then
       echo "Deploying $COMPONENT"
       terraform apply --auto-approve --var-file=tfvars/$TFVARS_FILENAME
       kubectl get all -A
    elif [ "$ACTION" = "destroy" ]; then
       echo "Destroying $COMPONENT"
       terraform destroy --auto-approve --var-file=tfvars/$TFVARS_FILENAME
    fi
fi
