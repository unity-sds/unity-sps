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
# -c: collection identifier for process task created collection and stage out task upload
# -b: stage out s3 bucket to upload processed data to
# -a: Cloudtamer API key with permissions to retrieve temporary AWS credentials
# -s: AWS account ID to retrieve credentials for

# API credential retrieval
CLOUDTAMER_API_URL="https://login.mcp.nasa.gov/api/v3"
CLOUDTAMER_ROLE="mcp-tenantOperator"

# Must be the same as the path of the Persistent Volume mounted by the Airflow KubernetesPodOperator
# that executes this script
WORKING_DIR="/scratch"

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

get_aws_credentials() {
  local cloudtamer_api_key=$1
  local aws_account_id=$2
  response=$(
    curl -s \
    -XPOST \
        -H "accept: application/json" \
        -H "Authorization: Bearer ${cloudtamer_api_key}" \
        -H "Content-Type: application/json" \
        "${CLOUDTAMER_API_URL}/temporary-credentials" \
        -d "{\"account_number\": \"$aws_account_id\",\"iam_role_name\": \"$CLOUDTAMER_ROLE\"}"
  )

  access_key_id=$(echo $response | jq -r .data.access_key)
  secret_access_key=$(echo $response | jq -r .data.secret_access_key)
  session_token=$(echo $response | jq -r .data.session_token)
  echo $access_key_id,$secret_access_key,$session_token
}

set -ex
while getopts i:k:w:j:e:o:c:b:a:s: flag
do
  case "${flag}" in
    i) cwl_workflow_stage_in=${OPTARG};;
    k) job_args_stage_in=${OPTARG};;
    w) cwl_workflow_process=${OPTARG};;
    j) job_args_process=${OPTARG};;
    e) ecr_login=${OPTARG};;
    o) json_output=${OPTARG};;
    c) collection_id=${OPTARG};;
    b) bucket=${OPTARG};;
    a) api_key=${OPTARG};;
    s) aws_account_id=${OPTARG};;
  esac
done

# create working directory if it doesn't exist
mkdir -p "$WORKING_DIR"
cd $WORKING_DIR

# stage in job args
rm -f ./job_args_stage_in.json
job_args_stage_in="$(get_job_args "$job_args_stage_in" stage_in)"
echo JOB_ARGS_STAGE_IN $job_args_stage_in
echo "Executing the CWL workflow: $cwl_workflow_stage_in with json arguments: $job_args_stage_in and working directory: $WORKING_DIR"

# process job args
rm -rf ./job_args_process.json
job_args_process="$(get_job_args "$job_args_process" process)"
echo "Executing the CWL workflow: $cwl_workflow_process with json arguments: $job_args_process and working directory: $WORKING_DIR"

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
stage_in=$(cwltool --outdir stage_in --copy-output stage_in.cwl test/ogc_app_package/stage_in.yml)

# Get directory that contains downloads
stage_in_dir=$(echo $stage_in | jq '.stage_in_download_dir.basename')
stage_in_dir="$PWD/stage_in/$(echo "$stage_in_dir" | tr -d '"')"
echo "Stage in download directory: $stage_in_dir"
ls -l $stage_in_dir/

# Remove extraneous directory in front of catalog.json
echo "Editing stage in catalog.json"
./entrypoint_utils.py -c "$stage_in_dir/catalog.json"

# Add input directory and output collection into process job arguments
echo "Editing process $job_args_process"
./entrypoint_utils.py -j $job_args_process -i $stage_in_dir -d $collection_id

# Process operations
process=$(cwltool process.cwl $job_args_process)

# Get directory that contains processed files
process_dir=$(echo $process | jq '.output.basename')
process_dir="$PWD/$(echo "$process_dir" | tr -d '"')"
echo "Process output directory: $process_dir"
ls -l $process_dir

# Stage out operations
credentials="$(get_aws_credentials "$api_key" "$aws_account_id")"
aws_key="$(cut -d ',' -f 1 <<< $credentials)"
aws_secret="$(cut -d ',' -f 2 <<< $credentials)"
aws_token="$(cut -d ',' -f 3 <<< $credentials)"
stage_out=$(cwltool stage_out.cwl \
                  --output_dir $process_dir \
                  --staging_bucket $bucket \
                  --collection_id $collection_id \
                  --aws_access_key_id $aws_key \
                  --aws_secret_access_key $aws_secret \
                  --aws_session_token $aws_token)
stage_out=$(echo "$stage_out" | jq 'map(.path)' | tr -d "[]\",\\t ")
echo "Stage out files: $stage_out"

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
