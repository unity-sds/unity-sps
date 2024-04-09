output "resources" {
  description = "SSM parameter IDs for pipeline resources."
  value = {
    "endpoints" = {
      "airflow"       = module.unity-sps-airflow.airflow_urls
      "ogc_processes" = module.unity-sps-airflow.ogc_processes_api_url
    }
    "buckets" = module.unity-sps-airflow.s3_buckets
  }
}
