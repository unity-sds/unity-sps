<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | ~> 1.8.2 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | 5.50.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.50.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_s3_bucket_notification"></a> [s3\_bucket\_notification](#module\_s3\_bucket\_notification) | git@github.com:unity-sds/unity-initiator.git//terraform-unity/triggers/s3-bucket-notification | 413-submit-ogc |
| <a name="module_unity_initiator"></a> [unity\_initiator](#module\_unity\_initiator) | git@github.com:unity-sds/unity-initiator.git//terraform-unity/initiator | 413-submit-ogc |

## Resources

| Name | Type |
|------|------|
| [aws_s3_bucket.code](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket.config](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket.inbound_staging_location](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/s3_bucket) | resource |
| [aws_s3_object.isl_stacam_rawdp_folder](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/s3_object) | resource |
| [aws_s3_object.router_config](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/resources/s3_object) | resource |
| [aws_ssm_parameter.airflow_api_url](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/ssm_parameter) | data source |
| [aws_ssm_parameter.ogc_processes_api_url](https://registry.terraform.io/providers/hashicorp/aws/5.50.0/docs/data-sources/ssm_parameter) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_airflow_api_url_ssm_param"></a> [airflow\_api\_url\_ssm\_param](#input\_airflow\_api\_url\_ssm\_param) | The SSM parameter name for the Airflow API URL | `string` | n/a | yes |
| <a name="input_airflow_webserver_password"></a> [airflow\_webserver\_password](#input\_airflow\_webserver\_password) | The password for the Airflow webserver and UI. | `string` | n/a | yes |
| <a name="input_airflow_webserver_username"></a> [airflow\_webserver\_username](#input\_airflow\_webserver\_username) | The username for the Airflow webserver and UI. | `string` | n/a | yes |
| <a name="input_ogc_processes_api_url_ssm_param"></a> [ogc\_processes\_api\_url\_ssm\_param](#input\_ogc\_processes\_api\_url\_ssm\_param) | The SSM parameter name for the OGC Processes API URL | `string` | n/a | yes |
| <a name="input_project"></a> [project](#input\_project) | The project or mission deploying Unity SPS | `string` | n/a | yes |
| <a name="input_release"></a> [release](#input\_release) | The software release version. | `string` | n/a | yes |
| <a name="input_service_area"></a> [service\_area](#input\_service\_area) | The service area owner of the resources being deployed | `string` | n/a | yes |
| <a name="input_venue"></a> [venue](#input\_venue) | The MCP venue in which the cluster will be deployed (dev, test, prod) | `string` | n/a | yes |

## Outputs

No outputs.
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
