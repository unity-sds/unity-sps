output "ogc_processes_urls" {
  description = "SSM parameter IDs and URLs for the various OGC Processes endpoints."
  value = {
    "ui" = {
      "ssm_param_id" = aws_ssm_parameter.ogc_processes_ui_url.id,
      "url"          = nonsensitive(aws_ssm_parameter.ogc_processes_ui_url.value)
    }
    "rest_api" = {
      "ssm_param_id" = aws_ssm_parameter.ogc_processes_api_url.id,
      "url"          = nonsensitive(aws_ssm_parameter.ogc_processes_api_url.value)
    }
  }
}
