#!/bin/sh
# Script to execute a CWL workflow that includes Docker containers
# The Docker engine is started before the CWL execution, and stopped afterwards.
# -i: The CWL workflow URL for the stage in task
# -s: STAC JSON URL or JSON data that describes input data requiring download
# -w: the CWL workflow URL for the process task
#     (example: https://github.com/unity-sds/sbg-workflows/blob/main/L1-to-L2-e2e.cwl)
# -j: a) the CWL process job parameters as a JSON formatted string
#        (example: { "name": "John Doe" })
#  OR b) The URL of a YAML or JSON file containing the job parameters
#        (example: https://github.com/unity-sds/sbg-workflows/blob/main/L1-to-L2-e2e.dev.yml)
# -o: The CWL workflow URL for the stage out task
# -d: The CWL stage out job parameters as a JSON formatted string
# -e: the ECR login URL where the AWS account ID and region are specific to the Airflow installation
#        (example: <aws_account_id>.dkr.ecr.<region>.amazonaws.com) [optional]
# -f: path to an output JSON file that needs to be shared as Airflow "xcom" data [optional]

# Can be the same as the path of the Persistent Volume mounted by the Airflow KubernetesPodOperator
# that executes this script to execute on EFS.
WORKING_DIR="/data"    # Set to EBS directory

get_job_args() {
  local job_args=$1
  workflow=$2
  # switch between the 2 cases a) and b) for job_args
  # remove arguments from previous tasks
  if [ "$job_args" = "${job_args#{}" ]
  then
    # job_args does NOT start with '{'
    job_args_file=$job_args
  else
    # job_args starts with '{'
    echo "$job_args" > ./job_args_$workflow.json
    job_args_file="./job_args_$workflow.json"
  fi
  echo $job_args_file
}

set -ex
while getopts i:s:w:j:o:d:e:f: flag
do
  case "${flag}" in
    i) cwl_workflow_stage_in=${OPTARG};;
    s) stac_json=${OPTARG};;
    w) cwl_workflow_process=${OPTARG};;
    j) job_args_process=${OPTARG};;
    o) cwl_workflow_stage_out=${OPTARG};;
    d) job_args_stage_out=${OPTARG};;
    e) ecr_login=${OPTARG};;
    f) json_output=${OPTARG};;
  esac
done

# create working directory if it doesn't exist
mkdir -p "$WORKING_DIR"
cd $WORKING_DIR

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

# Stage in operations
echo "Executing the CWL workflow: $cwl_workflow_stage_in with STAC JSON: $stac_json and working directory: $WORKING_DIR"
stage_in=$(cwltool --outdir stage_in --copy-output $cwl_workflow_stage_in --download_dir granules --stac_json $stac_json)

# Retrieve directory that contains downloaded granules
stage_in_dir=$(echo $stage_in | jq '.download_dir.path')
stage_in_dir=$(echo "$stage_in_dir" | tr -d '"')
echo "Stage in download directory: $stage_in_dir"
ls -l $stage_in_dir/

# Format process job args
rm -rf ./job_args_process.json
job_args_process="$(get_job_args "$job_args_process" process)"

# Add granule directory into process job arguments
echo "Updating process arguments with input directory: $job_args_process"
job_args_process_updated=./job_args_process_updated.json
cat $job_args_process | jq --arg data_dir $stage_in_dir '. += {"input": {"class": "Directory", "path": $data_dir}}' > $job_args_process_updated
mv $job_args_process_updated $job_args_process
echo "Executing the CWL workflow: $cwl_workflow_process with json arguments: $job_args_process and working directory: $WORKING_DIR"

# Process operations
process=$(cwltool --outdir process $cwl_workflow_process $job_args_process)
echo $process

# Get directory that contains processed files
process_dir=$(echo $process | jq '.output.path')
process_dir=$(echo "$process_dir" | tr -d '"')
echo "Process output directory: $process_dir"
ls -l $process_dir

# Add process directory into stage out job arguments
echo "Editing stage out arguments: $job_args_stage_out"
echo $job_args_stage_out | jq --arg data_dir $process_dir '. += {"sample_output_data": {"class": "Directory", "path": $data_dir}}' > ./job_args_stage_out.json
echo "Executing the CWL workflow: $cwl_workflow_stage_out with json arguments: job_args_stage_out.json and working directory: $WORKING_DIR"

# Stage out operations
stage_out=$(cwltool --outdir stage_out $cwl_workflow_stage_out job_args_stage_out.json)

# Report on stage out
successful_features=$(echo "$stage_out" | jq '.successful_features.path' | tr -d "[]\",\\t ")
successful_features=$(cat $successful_features | jq '.')
echo Successful features: $successful_features

failed_features=$(echo "$stage_out" | jq '.failed_features.path' | tr -d "[]\",\\t ")
failed_features=$(cat $failed_features | jq '.')
echo Failed features: $failed_features

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
