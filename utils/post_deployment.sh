#!/bin/bash
#set -ex

# Script to execute post-deployment operations
# Pre-Requisites:
# - SPS has been deployed successfully
# - AWS credentials are renewed and set in the environment
# Syntax:
# ./post_deployment.sh <WPST_API>
# Example:
# ./post_deployment.sh http://k8s-airflow-ogcproce-944e409e1d-687289935.us-west-2.elb.amazonaws.com:5001

# script argument: the $WPST_API
export WPST_API=$1

# list of processes to be registered
declare -a procs=("cwl_dag" "karpenter_test" "sbg_preprocess_cwl_dag" "cwl_high_workload_dag")

for proc in "${procs[@]}"
do
   echo " "
   # register process
   echo "Registering process: $proc"
   curl -X POST -H "Content-Type: application/json; charset=utf-8" --data '{"id":"'${proc}'", "version": "1.0.0"}'  "${WPST_API}/processes"
   # unregister process
   # echo "Unregistering process: $proc"
   # curl -X DELETE -H "Content-Type: application/json; charset=utf-8" "${WPST_API}/processes/${proc}"
   echo " "
done
