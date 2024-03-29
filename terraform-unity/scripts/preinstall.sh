#!/bin/bash

env

pushd $WORKDIR/modules/terraform-eks-cluster
    terraform apply -var "deployment_name=${DISPLAYNAME}" -var "venue=${VENUE}"
    terraform output > tf.output
    export CLUSTER_NAME=$(awk '/cluster_name/{print $NF}' tf.output)
    export COUNTER=$(awk '/counter/{print $NF}' tf.output)
popd

mkdir $WORKDIR/k8s $WORKDIR/tfvars
aws eks update-kubeconfig --name "${CLUSTER_NAME}" --kubeconfig $WORKDIR/k8s/$DISPLAYNAME.yml

# need airflow_webserver_password, eks cluster name, counter
cat <<EOF > terraform.tfvars
kubeconfig_filepath="${WORKDIR}/k8s/${DISPLAYNAME}.yml"
eks_cluster_name="${CLUSTER_NAME}"
counter="${COUNTER}"
airflow_webserver_password="spsIStheBEST!"
EOF