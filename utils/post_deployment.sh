#!/bin/bash
#set -ex

# Script to execute post-deployment operations
# Pre-Requisites:
# - SPS has been deployed successfully
# - AWS credentials are renewed and set in the environment
# Syntax:
# ./post_deployment.sh <WPST_API> (NO trailing slash!)
# Example:
# ./post_deployment.sh https://k8s-airflow-ogcproce-944e409e1d-687289935.us-west-2.elb.amazonaws.com:5001

# script argument: the $WPST_API
export WPST_API=$1

# list of processes to be registered
declare -a procs=("cwl_dag.json" "karpenter_test.json" "sbg_preprocess_cwl_dag.json")

for proc in "${procs[@]}"
do
   echo " "
   proc_name=$(echo "$proc" | sed "s/.json//")

   # register process
   echo "Registering process: $proc_name"
   curl -k -v -X POST -H "Expect:" -H "Content-Type: application/json; charset=utf-8" --data-binary @"../ogc-application-packages/$proc" "${WPST_API}/processes"

   # unregister process
   #echo "Unregistering process: $proc_name"
   #curl -k -X DELETE -H "Content-Type: application/json; charset=utf-8" "${WPST_API}/processes/${proc_name}"

done
