"""
Python module containing Unity/SPS/Airflow utilities
Example: get_node_affinity(capacity_type=["spot"], instance_family=["r6a"], instance_cpu=["4"])
"""


def get_node_affinity(capacity_type: list[str], instance_family=list[str], instance_cpu=list[str]):
    affinity = {
        "nodeAffinity": {
            "preferredDuringSchedulingIgnoredDuringExecution": [],
            "requiredDuringSchedulingIgnoredDuringExecution": {
                "nodeSelectorTerms": [{"matchExpressions": []}]
            },
        }
    }
    if capacity_type:
        affinity["nodeAffinity"]["preferredDuringSchedulingIgnoredDuringExecution"].append(
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
        )
    if instance_family:
        affinity["nodeAffinity"]["requiredDuringSchedulingIgnoredDuringExecution"]["nodeSelectorTerms"][0][
            "matchExpressions"
        ].append({"key": "karpenter.k8s.aws/instance-family", "operator": "In", "values": instance_family})
    if instance_cpu:
        affinity["nodeAffinity"]["requiredDuringSchedulingIgnoredDuringExecution"]["nodeSelectorTerms"][0][
            "matchExpressions"
        ].append({"key": "karpenter.k8s.aws/instance-cpu", "operator": "In", "values": instance_cpu})

    return affinity
