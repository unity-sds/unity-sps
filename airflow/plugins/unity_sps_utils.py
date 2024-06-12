"""
Module containing common utilities for the Unity Science Processing System.
"""


def get_affinity(instance_type: list[str], capacity_type: list[str], anti_affinity_label: str = None) -> dict:
    """
    Function to create an affinity dictionary to specify which EC2 type the Kubernetes Pod should be running on.

    Args:
        instance_type: the possible EC2 types (e.g.: ["r7i.xlarge"])
        capacity_type: "spot" and/or "on-demand"
        anti_affinity_label: optional label to prevent 2 Pods with that label to be provisioned on the same Kubernetes node.

    Returns:
        the Kubernetes affinity dictionary to be added to the pod specification.

    """

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
                                "key": "karpenter.k8s.aws/instance-type",
                                "operator": "In",
                                "values": instance_type,
                            }
                        ]
                    }
                ]
            },
        },
    }

    # optionally add an anti_affinity_label to constraint each pod to be instantiated on a different node
    if anti_affinity_label:
        affinity["podAntiAffinity"] = {
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
        }

    return affinity
