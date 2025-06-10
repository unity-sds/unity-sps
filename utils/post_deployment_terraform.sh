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
# export TOKEN_URL=https://cognito-idp.{region}.amazonaws.com    (where region is the AWS region executing in)

# Remove trailing slash from API URL if present
OGC_PROCESSES_API="${OGC_PROCESSES_API%/}"

# Retrieve limited-lifetime token
echo "Fetching Cognito token..."
payload="{\"AuthParameters\":{\"USERNAME\":\"$UNITY_USERNAME\",\"PASSWORD\":\"$UNITY_PASSWORD\"},\"AuthFlow\":\"USER_PASSWORD_AUTH\",\"ClientId\":\"$UNITY_CLIENTID\"}"

token_response=$(curl -X POST \
    -H "X-Amz-Target: AWSCognitoIdentityProviderService.InitiateAuth" \
    -H "Content-Type: application/x-amz-json-1.1" \
    --data $payload \
    $TOKEN_URL)

token=$(echo $token_response | jq -r '.AuthenticationResult.AccessToken')
echo "Cognito token retrieved."

# list of processes to be registered
declare -a procs=("cwl_dag.json" "karpenter_test.json" "appgen_dag.json" "cwl_dag_modular.json" "db_cleanup_dag.json")

for proc in "${procs[@]}"
do
    echo " "
    proc_name=$(echo "$proc" | sed "s/.json//")

    # unregister process (in case it was already registered)
    echo "Unregistering process: $proc_name"
    curl -k -X DELETE \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json; charset=utf-8" \
        "${OGC_PROCESSES_API}/processes/${proc_name}"

    # register process
    echo "Registering process: $proc_name"
    curl -k -X POST \
        -H "Authorization: Bearer ${token}" \
        -H "Expect:" \
        -H "Content-Type: application/json; charset=utf-8" \
        --data-binary @"../ogc-application-packages/$proc" \
        "${OGC_PROCESSES_API}/processes"
    echo " "

done
