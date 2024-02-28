output "airflow_webserver_url" {
  description = "The URL of the Airflow webserver service"
  value       = "http://${data.kubernetes_ingress_v1.airflow_ingress.status[0].load_balancer[0].ingress[0].hostname}:5000"
}

output "ogc_processes_api_url" {
  description = "The URL of the OGC Processes API service"
  value       = "http://${data.kubernetes_ingress_v1.ogc_processes_api_ingress.status[0].load_balancer[0].ingress[0].hostname}:5001"
}
