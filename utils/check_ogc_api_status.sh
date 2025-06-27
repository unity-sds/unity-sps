#!/bin/bash

# Remove trailing slash from API URL if present
OGC_PROCESSES_API="${OGC_PROCESSES_API%/}"
echo $OGC_PROCESSES_API
echo $TOKEN_URL

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

# Poll onto OGC API is available
response_status=0
while [ $response_status -ne 200 ]; do
    response_status=$(curl -s -o /dev/null -k -X GET -H "Authorization: Bearer ${token}" -w "%{http_code}" "${OGC_PROCESSES_API}/processes")
    echo "response_status=$response_status"
    sleep 10
done

exit 0
