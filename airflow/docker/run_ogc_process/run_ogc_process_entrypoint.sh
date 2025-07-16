#!/bin/sh

set -e

if [ "$SUBMIT_JOB" = "true" ] || [ "$SUBMIT_JOB" = "True" ]; then
    echo "Submitting job"

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
elif [ "$SUBMIT_JOB" = "false" ] || [ "$SUBMIT_JOB" = "False" ]; then
    echo "Monitoring job status"
    echo "graceal job id in the entrypiont is $JOB_ID"
    MONITOR_JOB_URL=$(echo "$MONITOR_JOB_URL" | sed "s/{job_id}/$JOB_ID/")
    echo "graceal the monitor job url is $MONITOR_JOB_URL"
    TIMEOUT=3600
    POLL_INTERVAL=30
    SECONDS=0
    
    while [ $SECONDS -lt $TIMEOUT ]; do
        echo "Checking status..."
        response=$(curl --location ${MONITOR_JOB_URL} \
        --header "proxy-ticket: ${MAAP_PGT}" \
        --header "Content-Type: application/json")

        status=$(echo "$response" | jq -r .status)
        
        echo "Current status is: $status"
        
        if [ "$status" = "successful" ]; then
            echo "Job completed successfully!"
            exit 0
        elif [ "$status" = "failed" ]; then
            echo "Job failed!"
            echo "Error details: $(echo "$response" | jq .)"
            exit 0 # TODO should this be 1 or 0?
        fi
        
        sleep $POLL_INTERVAL
        SECONDS=$((SECONDS + POLL_INTERVAL))
    done
    
    echo "Job monitoring timed out after $TIMEOUT seconds."
    exit 1
else
    echo "SUBMIT_JOB variable must be specified and set to true or false"
fi