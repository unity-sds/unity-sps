#!/bin/sh
# Script to execute a CWL workflow that includes Docker containers
# The Docker engine is started before the CWL execution, and stopped afterwards.
# $1: the CWL workflow URL
#     (example: https://github.com/unity-sds/sbg-workflows/blob/main/L1-to-L2-e2e.cwl)
# $2: a) the CWL job parameters as a JSON formatted string
#        (example: { "name": "John Doe" })
#  OR b) The URL of a YAML or JSON file containing the job parameters
#        (example: https://github.com/unity-sds/sbg-workflows/blob/main/L1-to-L2-e2e.dev.yml)
# $3: optional path to an output JSON file that needs to be shared as Airflow "xcom" data

# Must be the same as the path of the Persistent Volume mounted by the Airflow KubernetesPodOperator
# that executes this script
WORKING_DIR="/scratch"

set -ex
cwl_workflow=$1
job_args=$2
json_output=$3

# create working directory if it doesn't exist
mkdir -p "$WORKING_DIR"
cd $WORKING_DIR

# switch between the 2 cases a) and b) for job_args
# remove arguments from previous tasks
rm -f ./job_args.json
if [ "$job_args" = "${job_args#{}" ]
then
  # job_args does NOT start with '{'
  echo "Using job arguments from URL: $job_args"
else
  # job_args starts with '{'
  echo "$job_args" > ./job_args.json
  echo "Using job arguments from JSON string:" && cat ./job_args.json
  job_args="./job_args.json"
fi
echo "Executing the CWL workflow: $cwl_workflow with json arguments: $job_args and working directory: $WORKING_DIR"
echo "JSON XCOM output: ${json_output}"

# Start Docker engine
dockerd &> dockerd-logfile &

# Wait until Docker engine is running
# Loop until 'docker version' exits with 0.
until docker version > /dev/null 2>&1
do
  sleep 1
done

# Execute CWL workflow in working directory
# List contents when done
. /usr/share/cwl/venv/bin/activate
pwd
ls -lR
cwl-runner --tmp-outdir-prefix "$PWD"/ --no-read-only "$cwl_workflow" "$job_args"
ls -lR

# Optionally, save the requested output file to a location
# where it will be picked up by the Airflow XCOM mechanism
# Note: the content of the file MUST be valid JSON or XCOM will fail.
if [ ! -z "${json_output}" -a "${json_output}" != " " ]; then
  mkdir -p /airflow/xcom/
  cp ${json_output} /airflow/xcom/return.json
fi

deactivate

# Stop Docker engine
pkill -f dockerd
