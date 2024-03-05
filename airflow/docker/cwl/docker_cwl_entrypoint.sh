#!/bin/sh
# Script to execute a CWL workflow that includes Docker containers
# The Docker engine is started before the CWL execution, and stopped afterwards.
# $1: the CWL workflow URL
#     (example: https://github.com/unity-sds/sbg-workflows/blob/main/L1-to-L2-e2e.cwl)
# $2: a) the CWL job parameters as a JSON formatted string
#        (example: { "name": "John Doe" })
#  OR b) The URL of a YAML or JSON file containing the job parameters
#        (example: https://github.com/unity-sds/sbg-workflows/blob/main/L1-to-L2-e2e.dev.yml)
# $3: optional output directory, defaults to the current directory
# Note: $output_dir must be accessible by the Docker container that executes this script

set -e
cwl_workflow=$1
job_args=$2
output_dir=${3:-.}

# switch between the 2 cases a) and b) for job_args
if [ "$job_args" = "${job_args#{}" ]
then
  # job_args does NOT start with '{'
  echo "Using job arguments from URL: $job_args"
else
  echo "$job_args" > /tmp/job_args.json
  echo "Using job arguments from JSON string:" && cat /tmp/job_args.json
  job_args="/tmp/job_args.json"
fi
echo "Executing the CWL workflow: $cwl_workflow with json arguments: $job_args and output directory: $output_dir"

# create output directory if it doesn't exist
mkdir -p "$output_dir"

# Start Docker engine
dockerd &> dockerd-logfile &

# Wait until Docker engine is running
# Loop until 'docker version' exits with 0.
until docker version > /dev/null 2>&1
do
  sleep 1
done

# Execute CWL workflow
. /usr/share/cwl/venv/bin/activate
cwl-runner --outdir "$output_dir" "$cwl_workflow" "$job_args"
deactivate

# Stop Docker engine
pkill -f dockerd
