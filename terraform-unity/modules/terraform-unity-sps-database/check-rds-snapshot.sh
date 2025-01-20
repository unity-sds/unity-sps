#!/bin/bash

db_id=$1

if [ -z ${db_id} ]; then
  echo "usage : $0 <db_id>" >2
  exit 1
fi

RESULT=($(aws rds describe-db-snapshots --db-instance-identifier $db_id --output text --region us-west-2 2> /dev/null))
aws_result=$?

if [ ${aws_result} -eq 0 ] && [[ ${RESULT[0]} == "DBSNAPSHOTS" ]]; then
  result='true'
else
  result='false'
fi

jq -n --arg exists ${result} '{"db_exists": $exists }'
