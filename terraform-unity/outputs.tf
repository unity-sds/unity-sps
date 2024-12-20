output "resources" {
  description = "SSM parameter IDs for SPS resources."
  value = {
    "endpoints" = {
      "airflow"       = module.unity-sps-airflow.airflow_urls
      "ogc_processes" = module.unity-sps-ogc-processes-api.ogc_processes_urls
    }
    "venue_endpoints" = {
      "airflow"       = module.unity-sps-airflow.airflow_venue_urls
      "ogc_processes" = module.unity-sps-ogc-processes-api.ogc_processes_venue_urls
    }
    "buckets" = module.unity-sps-airflow.s3_buckets
  }
}
