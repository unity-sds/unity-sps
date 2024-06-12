"""
Module containing common utilities for the Unity Science Processing System.
"""


def get_affinity(
    capacity_type: list[str], instance_family: list[str], instance_cpu: list[str], anti_affinity_label: str
):

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
                                "key": "karpenter.k8s.aws/instance-family",
                                "operator": "In",
                                "values": instance_family,
                            },
                            {
                                "key": "karpenter.k8s.aws/instance-cpu",
                                "operator": "In",
                                "values": instance_cpu,
                            },
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
