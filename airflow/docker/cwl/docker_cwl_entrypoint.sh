#!/bin/sh
# Script to execute a CWL workflow that includes Docker containers
# The Docker engine is started before the CWL execution, and stopped afterwards.
# $1: the CWL workflow URL (example: https://raw.githubusercontent.com/unity-sds/unity-sps-prototype/cwl-docker/cwl/cwl_workflows/echo_from_docker.cwl)
# $2: the CWL job parameters as a JSON formatted string (example: { name: John Doe })
# $3: optional output directory, defaults to the current directory
# Note: $output_dir must be accessible by the Docker container that executes this script

set -ex
cwl_workflow=$1
job_args=$2
output_dir=${3:-.}
echo "Executing CWL workflow: $cwl_workflow with json arguments: $job_args and output directory: $output_dir"
echo "$job_args" > /tmp/job_args.json
cat /tmp/job_args.json

# create output directory if it doesn't exist
mkdir -p "$output_dir"

# Start Docker engine
dockerd > dockerd-logfile 2>&1

# Wait until Docker engine is running
# Loop until 'docker version' exits with 0.
until docker version > /dev/null 2>&1
do
  sleep 1
done

# Execute CWL workflow
. /usr/share/cwl/venv/bin/activate
cwl-runner --outdir "$output_dir" --no-match-user --no-read-only "$cwl_workflow" /tmp/job_args.json
deactivate

# Stop Docker engine
pkill -f dockerd
