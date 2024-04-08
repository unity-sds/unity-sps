#!/bin/bash

aws eks update-kubeconfig --name "${CLUSTER_NAME}" --kubeconfig $WORKDIR/k8s/$DISPLAYNAME.yml