resource "aws_s3_bucket" "inbound_staging_location" {
  bucket        = format(local.resource_name_prefix, "isl")
  force_destroy = true
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "S3-ISL")
    Component = "S3"
    Stack     = "S3"
  })
}

resource "aws_s3_bucket" "code" {
  bucket        = format(local.resource_name_prefix, "code")
  force_destroy = true
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "S3-code")
    Component = "S3"
    Stack     = "S3"
  })
}

resource "aws_s3_bucket" "config" {
  bucket        = format(local.resource_name_prefix, "config")
  force_destroy = true
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "S3-config")
    Component = "S3"
    Stack     = "S3"
  })
}

resource "aws_s3_bucket_policy" "ssl_s3_policy" {
  for_each = toset([
    "isl",
    "code",
    "config"
  ])
  bucket = format(local.resource_name_prefix, each.key)
  policy = jsonencode(
    {
      "Id" : "ExamplePolicy",
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Sid" : "AllowSSLRequestsOnly",
          "Action" : "s3:*",
          "Effect" : "Deny",
          "Resource" : [
            format("%s%s", "arn:aws:s3:::", format(local.resource_name_prefix, each.key)),
            format("%s%s/%s", "arn:aws:s3:::", format(local.resource_name_prefix, each.key), "*")
          ],
          "Condition" : {
            "Bool" : {
              "aws:SecureTransport" : "false"
            }
          },
          "Principal" : "*"
        }
      ]
    }
  )
}


resource "aws_s3_object" "router_config" {
  bucket = aws_s3_bucket.config.id
  key    = "routers/srl_router.yaml"
  content = templatefile("${path.module}/../../../unity-initiator/routers/srl_router.tmpl.yaml", {
    airflow_base_api_endpoint       = data.aws_ssm_parameter.airflow_api_url.value
    airflow_username                = var.airflow_webserver_username
    airflow_password                = var.airflow_webserver_password
    ogc_processes_base_api_endpoint = data.aws_ssm_parameter.ogc_processes_api_url.value
  })
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "S3-router")
    Component = "S3"
    Stack     = "S3"
  })
}

module "unity_initiator" {
  source        = "git@github.com:unity-sds/unity-initiator.git//terraform-unity/initiator?ref=unity-sps-2.2.0"
  code_bucket   = aws_s3_bucket.code.id
  project       = var.project
  router_config = "s3://${aws_s3_bucket.config.id}/${aws_s3_object.router_config.key}"
  venue         = var.venue
}

resource "aws_s3_object" "isl_stacam_rawdp_folder" {
  bucket = aws_s3_bucket.inbound_staging_location.id
  key    = "STACAM/RawDP/"
}

module "s3_bucket_notification" {
  source              = "git@github.com:unity-sds/unity-initiator.git//terraform-unity/triggers/s3-bucket-notification?ref=unity-sps-2.2.0"
  initiator_topic_arn = module.unity_initiator.initiator_topic_arn
  isl_bucket          = aws_s3_bucket.inbound_staging_location.id
  isl_bucket_prefix   = "STACAM/RawDP/"
}
