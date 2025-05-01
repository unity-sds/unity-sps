"""
Module containing common utilities for the Unity Science Processing System.
"""

import os

from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s

# Shared constants
POD_NAMESPACE = "sps"  # The Kubernetes namespace within which the Pod is run (it must already exist)
POD_LABEL = "cwl_task"

# Note: each Pod is assigned the same label to assure that (via the anti-affinity requirements)
# two Pods with the same label cannot run on the same Node
SPS_DOCKER_CWL_IMAGE = "ghcr.io/unity-sds/unity-sps/sps-docker-cwl:2.6.4"

NODE_POOL_DEFAULT = "airflow-kubernetes-pod-operator"
NODE_POOL_HIGH_WORKLOAD = "airflow-kubernetes-pod-operator-high-workload"

CS_SHARED_SERVICES_ACCOUNT_ID = "/unity/shared-services/aws/account"
CS_SHARED_SERVICES_ACCOUNT_REGION = "/unity/shared-services/aws/account/region"
DS_COGNITO_CLIENT_ID = "/unity/shared-services/dapa/client-id"
DS_S3_BUCKET_PARAM = f"/unity/unity/{os.environ['AIRFLOW_VAR_UNITY_VENUE']}/ds/datastore-bucket"

DEFAULT_LOG_LEVEL = "INFO"
LOG_LEVEL_TYPE = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}

EC2_TYPES = {
    # "t3.nano": {
    #     "desc": "General Purpose",
    #     "cpu": 1,
    #     "memory": 0.5,
    # },
    # "t3.micro": {
    #     "desc": "General Purpose",
    #     "cpu": 2,
    #     "memory": 1,
    # },
    "t3.small": {
        "desc": "General Purpose",
        "cpu": 2,
        "memory": 2,
    },
    "t3.medium": {
        "desc": "General Purpose",
        "cpu": 2,
        "memory": 4,
    },
    "t3.large": {
        "desc": "General Purpose",
        "cpu": 2,
        "memory": 8,
    },
    "t3.xlarge": {
        "desc": "General Purpose",
        "cpu": 4,
        "memory": 16,
    },
    "t3.2xlarge": {
        "desc": "General Purpose",
        "cpu": 8,
        "memory": 32,
    },
    "r7i.xlarge": {
        "desc": "Memory Optimized",
        "cpu": 4,
        "memory": 32,
    },
    "r7i.2xlarge": {
        "desc": "Memory Optimized",
        "cpu": 8,
        "memory": 64,
    },
    "r7i.4xlarge": {
        "desc": "Memory Optimized",
        "cpu": 16,
        "memory": 128,
    },
    "r7i.8xlarge": {
        "desc": "Memory Optimized",
        "cpu": 32,
        "memory": 256,
    },
    "c6i.xlarge": {
        "desc": "Compute Optimized",
        "cpu": 4,
        "memory": 8,
    },
    "c6i.2xlarge": {
        "desc": "Compute Optimized",
        "cpu": 8,
        "memory": 16,
    },
    "c6i.4xlarge": {
        "desc": "Compute Optimized",
        "cpu": 16,
        "memory": 32,
    },
    "c6i.8xlarge": {
        "desc": "Compute Optimized",
        "cpu": 32,
        "memory": 64,
    },
    "c6i.12xlarge": {
        "desc": "Compute Optimized",
        "cpu": 48,
        "memory": 96,
    },
    "c6i.16xlarge": {
        "desc": "Compute Optimized",
        "cpu": 64,
        "memory": 128,
    },
    "c6id.xlarge": {
        "desc": "Compute Optimized with SSD local storage",
        "cpu": 4,
        "memory": 8,
    },
    "c6id.2xlarge": {
        "desc": "Compute Optimized with SSD local storage",
        "cpu": 8,
        "memory": 16,
    },
    "c6id.4xlarge": {
        "desc": "Compute Optimized with SSD local storage",
        "cpu": 16,
        "memory": 32,
    },
    "m5ad.xlarge": {
        "desc": "General Purpose with SSD local storage",
        "cpu": 4,
        "memory": 16,
    },
    "m5ad.2xlarge": {
        "desc": "General Purpose with SSD local storage",
        "cpu": 8,
        "memory": 32,
    },
    "m5ad.4xlarge": {
        "desc": "General Purpose with SSD local storage",
        "cpu": 16,
        "memory": 64,
    },
}


def build_ec2_type_label(key):
    return f"{key} ({EC2_TYPES.get(key)['desc']}: {EC2_TYPES.get(key)['cpu']}vCPU, {EC2_TYPES.get(key)['memory']}GiB)"


class SpsKubernetesPodOperator(KubernetesPodOperator):
    """
    Subclass of KubernetesPodOperator that adds more fields for Jinja templating.
    """

    template_fields = KubernetesPodOperator.template_fields + ("node_selector", "affinity")


def get_affinity(
    capacity_type: list[str] = None, instance_type: list[str] = None, anti_affinity_label: str = None
) -> k8s.V1Affinity:
    """
    Function that builds a Kubernetes Pod affinity constraint for allocating
    Pods onto Kubernetes Nodes (eiter already available or to be provisioned).

    Parameters
    ----------
    capacity_type: list of "spot" and "on-demand" elements. Defaults to "spot"
    instance_type: optional list of specific EC2 types
    anti_affinity_label: optional label to guarantee that each Pod will be allocated to a separate Node

    Returns
    -------
    k8s.V1Affinity: object containing the Pod placement constraints

    """

    if capacity_type is None:
        capacity_type = ["spot"]
    node_constraints = [{"key": "karpenter.sh/capacity-type", "operator": "In", "values": capacity_type}]
    if instance_type is not None:
        node_constraints.append(
            {
                "key": "node.kubernetes.io/instance-type",
                "operator": "In",
                "values": instance_type,
            }
        )

    pod_anti_affinity = None
    if anti_affinity_label:
        pod_anti_affinity = k8s.V1PodAntiAffinity(
            required_during_scheduling_ignored_during_execution=[
                k8s.V1PodAffinityTerm(
                    k8s.V1LabelSelector(
                        match_expressions=[{"key": "pod", "operator": "In", "values": [anti_affinity_label]}]
                    ),
                    topology_key="kubernetes.io/hostname",
                ),
            ]
        )

    affinity = k8s.V1Affinity(
        node_affinity=k8s.V1NodeAffinity(
            required_during_scheduling_ignored_during_execution=k8s.V1NodeSelector(
                node_selector_terms=[
                    k8s.V1NodeSelectorTerm(
                        match_expressions=node_constraints,
                    )
                ]
            ),
        ),
        pod_anti_affinity=pod_anti_affinity,
    )

    return affinity
