airflow_docker_images = {
  "airflow" : {
    "name" : "ghcr.io/unity-sds/unity-sps/sps-airflow",
    "tag" : "2.5.3"
  }
}
airflow_webserver_password = ""
airflow_webserver_username = ""
dag_catalog_repo = {
  "dags_directory_path" : "airflow/dags",
  "ref" : "2.5.1",
  "url" : "https://github.com/unity-sds/unity-sps.git"
}
deployment_name = ""
helm_charts = {
  "airflow" : {
    "chart" : "airflow",
    "repository" : "https://airflow.apache.org",
    "version" : "1.15.0"
  },
  "keda" : {
    "chart" : "keda",
    "repository" : "https://kedacore.github.io/charts",
    "version" : "v2.15.1"
  }
}
installprefix = ""
karpenter_node_classes = {
  "airflow-kubernetes-pod-operator-high-workload" : {
    "volume_size" : "300Gi"
  },
  "default" : {
    "volume_size" : "30Gi"
  }
}
karpenter_node_pools = {
  "airflow-celery-workers" : {
    "disruption" : {
      "consolidateAfter" : "1m",
      "consolidationPolicy" : "WhenEmpty"
    },
    "limits" : {
      "cpu" : "800",
      "memory" : "3200Gi"
    },
    "nodeClassRef" : "default",
    "requirements" : [
      {
        "key" : "karpenter.k8s.aws/instance-family",
        "operator" : "In",
        "values" : [
          "m7i",
          "m6i",
          "m5",
          "t3",
          "c7i",
          "c6i",
          "c5",
          "r7i",
          "r6i",
          "r5"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-cpu",
        "operator" : "Gt",
        "values" : [
          "1"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-cpu",
        "operator" : "Lt",
        "values" : [
          "9"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-memory",
        "operator" : "Gt",
        "values" : [
          "8191"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-memory",
        "operator" : "Lt",
        "values" : [
          "32769"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-hypervisor",
        "operator" : "In",
        "values" : [
          "nitro"
        ]
      }
    ]
  },
  "airflow-core-components" : {
    "disruption" : {
      "consolidateAfter" : "1m",
      "consolidationPolicy" : "WhenEmpty"
    },
    "limits" : {
      "cpu" : "400",
      "memory" : "1600Gi"
    },
    "nodeClassRef" : "default",
    "requirements" : [
      {
        "key" : "karpenter.k8s.aws/instance-family",
        "operator" : "In",
        "values" : [
          "m7i",
          "m6i",
          "m5",
          "t3",
          "c7i",
          "c6i",
          "c5",
          "r7i",
          "r6i",
          "r5"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-cpu",
        "operator" : "Gt",
        "values" : [
          "1"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-cpu",
        "operator" : "Lt",
        "values" : [
          "17"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-memory",
        "operator" : "Gt",
        "values" : [
          "8191"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-memory",
        "operator" : "Lt",
        "values" : [
          "32769"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-hypervisor",
        "operator" : "In",
        "values" : [
          "nitro"
        ]
      }
    ]
  },
  "airflow-kubernetes-pod-operator" : {
    "disruption" : {
      "consolidateAfter" : "1m",
      "consolidationPolicy" : "WhenEmpty"
    },
    "limits" : {
      "cpu" : "10000",
      "memory" : "40000Gi"
    },
    "nodeClassRef" : "default",
    "requirements" : [
      {
        "key" : "karpenter.k8s.aws/instance-family",
        "operator" : "In",
        "values" : [
          "m7i",
          "m6i",
          "m5",
          "t3",
          "c7i",
          "c6i",
          "c5",
          "r7i",
          "r6i",
          "r5"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-cpu",
        "operator" : "Gt",
        "values" : [
          "1"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-cpu",
        "operator" : "Lt",
        "values" : [
          "17"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-memory",
        "operator" : "Gt",
        "values" : [
          "4095"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-memory",
        "operator" : "Lt",
        "values" : [
          "32769"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-hypervisor",
        "operator" : "In",
        "values" : [
          "nitro"
        ]
      }
    ]
  },
  "airflow-kubernetes-pod-operator-high-workload" : {
    "disruption" : {
      "consolidateAfter" : "1m",
      "consolidationPolicy" : "WhenEmpty"
    },
    "limits" : {
      "cpu" : "52800",
      "memory" : "105600Gi"
    },
    "nodeClassRef" : "airflow-kubernetes-pod-operator-high-workload",
    "requirements" : [
      {
        "key" : "karpenter.k8s.aws/instance-family",
        "operator" : "In",
        "values" : [
          "m7i",
          "m6i",
          "m5",
          "t3",
          "c7i",
          "c6i",
          "c5",
          "r7i",
          "r6i",
          "r5"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-cpu",
        "operator" : "Gt",
        "values" : [
          "1"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-cpu",
        "operator" : "Lt",
        "values" : [
          "65"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-memory",
        "operator" : "Gt",
        "values" : [
          "4095"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-memory",
        "operator" : "Lt",
        "values" : [
          "131073"
        ]
      },
      {
        "key" : "karpenter.k8s.aws/instance-hypervisor",
        "operator" : "In",
        "values" : [
          "nitro"
        ]
      }
    ]
  }
}
kubeconfig_filepath = "/Users/cinquini/PycharmProjects/unity-sps/terraform-unity/modules/terraform-unity-sps-eks/asips-int-sps-eks.cfg"
mcp_ami_owner_id    = "794625662971"
ogc_processes_docker_images = {
  "git_sync" : {
    "name" : "registry.k8s.io/git-sync/git-sync",
    "tag" : "v4.2.4"
  },
  "ogc_processes_api" : {
    "name" : "ghcr.io/unity-sds/unity-sps-ogc-processes-api/unity-sps-ogc-processes-api",
    "tag" : "2.0.0"
  },
  "redis" : {
    "name" : "redis",
    "tag" : "7.4.0"
  }
}
project      = "asips"
release      = "24.4"
service_area = "sps"
tags = {
  "empty" : ""
}
venue = "int"
