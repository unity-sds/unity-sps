"""
Module containing common utilities for the Unity Science Processing System.
"""

from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s


class SpsKubernetesPodOperator(KubernetesPodOperator):
    """
    Subclass of KubernetesPodOperator that adds more fields for Jinja templating.
    """

    template_fields = KubernetesPodOperator.template_fields + ("node_selector", "affinity")


def get_affinity2(capacity_type: list[str], anti_affinity_label: str):

    affinity = k8s.V1Affinity(
        node_affinity=k8s.V1NodeAffinity(
            required_during_scheduling_ignored_during_execution=k8s.V1NodeSelector(
                node_selector_terms=[
                    k8s.V1NodeSelectorTerm(
                        match_expressions=[
                            {"key": "karpenter.sh/capacity-type", "operator": "In", "values": [capacity_type]}
                        ]
                    )
                ]
            ),
        ),
        pod_anti_affinity=k8s.V1PodAntiAffinity(
            required_during_scheduling_ignored_during_execution=[
                k8s.V1PodAffinityTerm(
                    k8s.V1LabelSelector(
                        match_expressions=[{"key": "app", "operator": "In", "values": [anti_affinity_label]}]
                    ),
                    topology_key="kubernetes.io/hostname",
                ),
            ]
        ),
    )

    return affinity


def get_affinity(capacity_type: list[str], instance_type: list[str], anti_affinity_label: str):

    affinity = {
        "nodeAffinity": {
            "preferredDuringSchedulingIgnoredDuringExecution": [
                {
                    "weight": 1,
                    "preference": {
                        "matchExpressions": [
                            {
                                "key": "karpenter.sh/capacity-type",
                                "operator": "In",
                                "values": capacity_type,
                            }
                        ]
                    },
                }
            ],
            "requiredDuringSchedulingIgnoredDuringExecution": {
                "nodeSelectorTerms": [
                    {
                        "matchExpressions": [
                            {
                                "key": "node.kubernetes.io/instance-type",
                                "operator": "In",
                                "values": instance_type,
                            }
                        ]
                    }
                ]
            },
        },
        "podAntiAffinity": {
            "requiredDuringSchedulingIgnoredDuringExecution": [
                {
                    "labelSelector": {
                        "matchExpressions": [
                            {
                                "key": "app",
                                "operator": "In",
                                "values": [anti_affinity_label],
                            },
                        ]
                    },
                    "topologyKey": "kubernetes.io/hostname",
                }
            ]
        },
    }
    return affinity
