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
