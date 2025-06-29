#!/bin/bash
#set -ex

# Script to execute post-deployment operations.
# Pre-Requisites:
# - SPS has been deployed successfully to a given venue
# - The user has valid Cognito credentials for the target venue

# Syntax:
# cd unity-sps/utils
# export UNITY_USERNAME="....."
# export UNITY_PASSWORD="....."
# export UNITY_CLIENTID="...."
# export OGC_PROCESSES_API=https://.........execute-api.us-west-2.amazonaws.com/dev/ogc/api (NO trailing slash!)
# source ./post_deployment.sh

# Retrieve limited-lifetime token
export TOKEN="$(python cognito-token-fetch.py -u $UNITY_USERNAME  -c $UNITY_CLIENTID -p $UNITY_PASSWORD)"
echo $TOKEN

# list of processes to be registered
declare -a procs=("cwl_dag.json" "karpenter_test.json" "appgen_dag.json" "cwl_dag_modular.json" "db_cleanup_dag.json")

for proc in "${procs[@]}"
do
   echo " "
   proc_name=$(echo "$proc" | sed "s/.json//")

   # unregister process (in case it was already registered)
   echo "\nUnregistering process: $proc_name"
   curl -kv -X DELETE -H "${TOKEN}" -H "Content-Type: application/json; charset=utf-8" "${OGC_PROCESSES_API}/processes/${proc_name}"

   # register process
   echo "\nRegistering process: $proc_name"
   curl -k -v -X POST -H "${TOKEN}" -H "Expect:" -H "Content-Type: application/json; charset=utf-8" --data-binary @"../ogc-application-packages/$proc" "${OGC_PROCESSES_API}/processes"

done
