#!/bin/bash
mkdir $WORKDIR/k8s
aws eks update-kubeconfig --name $DISPLAYNAME --kubeconfig $WORKDIR/k8s/$DISPLAYNAME.yml
