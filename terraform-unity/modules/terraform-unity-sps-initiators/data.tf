data "aws_ssm_parameter" "airflow_api_url" {
  name = var.airflow_api_url_ssm_param
}

data "aws_ssm_parameter" "ogc_processes_api_url" {
  name = var.ogc_processes_api_url_ssm_param
}
