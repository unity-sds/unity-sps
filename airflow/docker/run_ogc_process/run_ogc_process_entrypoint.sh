#!/bin/sh

set -e

# Submit job to endpoint
SUBMIT_JOB_URL=$(echo "$SUBMIT_JOB_URL" | sed "s/{process_id}/$PROCESS_ID/")

echo "Submitting the job to ${SUBMIT_JOB_URL}"

response=$(curl --location ${SUBMIT_JOB_URL} \
--header "proxy-ticket: ${MAAP_PGT}" \
--header "Content-Type: application/json" \
--data "${JOB_INPUTS}")

echo "API Response: $response"
job_id=$(echo "$response" | jq -r .id)

if [ "$job_id" = "null" ] || [ -z "$job_id" ]; then
    echo "Failed to get jobID from response."
    exit 1
fi

echo "Job submitted successfully. Job ID: ${job_id}"

# Write the job_id to the XCom return file for the next task
mkdir -p /airflow/xcom/
printf '{"job_id": "%s"}' "$job_id" > /airflow/xcom/return.json