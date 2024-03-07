#!/bin/sh
# Script to execute a CWL workflow that includes Docker containers
# The Docker engine is started before the CWL execution, and stopped afterwards.
# $1: the CWL workflow URL
#     (example: https://github.com/unity-sds/sbg-workflows/blob/main/L1-to-L2-e2e.cwl)
# $2: a) the CWL job parameters as a JSON formatted string
#        (example: { "name": "John Doe" })
#  OR b) The URL of a YAML or JSON file containing the job parameters
#        (example: https://github.com/unity-sds/sbg-workflows/blob/main/L1-to-L2-e2e.dev.yml)
# $3: optional working directory, defaults to the current directory
# Note: The working must be accessible by the Docker container that executes this script

set -ex
cwl_workflow=$1
job_args=$2
work_dir=${3:-.}

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
echo "Executing the CWL workflow: $cwl_workflow with json arguments: $job_args and working directory: $work_dir"

# create working directory if it doesn't exist
mkdir -p "$work_dir"
cd $work_dir

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
pwd
mkdir -p ./cache
cwl-runner --cachedir ./cache --tmp-outdir-prefix "$PWD"/ "$cwl_workflow" "$job_args"
deactivate

# Stop Docker engine
pkill -f dockerd
