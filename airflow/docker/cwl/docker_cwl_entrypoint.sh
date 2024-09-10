#!/bin/sh
# Script to execute a CWL workflow that includes Docker containers
# The Docker engine is started before the CWL execution, and stopped afterwards.
# -w: the CWL workflow URL
#     (example: https://github.com/unity-sds/sbg-workflows/blob/main/L1-to-L2-e2e.cwl)
# -j: a) the CWL job parameters as a JSON formatted string
#        (example: { "name": "John Doe" })
#  OR b) The URL of a YAML or JSON file containing the job parameters
#        (example: https://github.com/unity-sds/sbg-workflows/blob/main/L1-to-L2-e2e.dev.yml)
# -e: the ECR login URL where the AWS account ID and region are specific to the Airflow installation
#        (example: <aws_account_id>.dkr.ecr.<region>.amazonaws.com) [optional]
# -o: path to an output JSON file that needs to be shared as Airflow "xcom" data [optional]

# Must be the same as the path of the Persistent Volume mounted by the Airflow KubernetesPodOperator
# that executes this script
WORKING_DIR="/scratch"

set -ex
while getopts w:j:e:o: flag
do
  case "${flag}" in
    w) cwl_workflow=${OPTARG};;
    j) job_args=${OPTARG};;
    e) ecr_login=${OPTARG};;
    o) json_output=${OPTARG};;
  esac
done

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

# Activate Python virtual environments for executables
. /usr/share/cwl/venv/bin/activate

# Log into AWS ECR repository
if [ "$ecr_login" != "None" ]; then
IFS=. read account_id dkr ecr aws_region amazonaws com <<EOF
${ecr_login}
EOF
aws ecr get-login-password --region $aws_region | docker login --username AWS --password-stdin $ecr_login
echo "Logged into: $ecr_login"
fi

# Execute CWL workflow in working directory
# List contents when done
pwd
ls -lR
cwl-runner --debug --tmp-outdir-prefix "$PWD"/ --no-read-only "$cwl_workflow" "$job_args"
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
