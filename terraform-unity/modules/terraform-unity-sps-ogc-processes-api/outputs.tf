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

output "ogc_processes_venue_urls" {
  description = "URLs for the various OGC Processes endpoints at venue-proxy level."
  value = {
    "ui" = {
      "url" = nonsensitive(replace(data.aws_ssm_parameter.venue_proxy_baseurl.value, "management/ui", "ogc/redoc"))
    }
    "rest_api" = {
      "url" = nonsensitive(replace(data.aws_ssm_parameter.venue_proxy_baseurl.value, "management/ui", "ogc/"))
    }
  }
}
