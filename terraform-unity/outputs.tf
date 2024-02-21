output "load_balancer_hostnames" {
  description = "Load Balancer Ingress Hostnames"
  value = {
    airflow = module.unity-sps-airflow.airflow_webserver_url
  }
}
