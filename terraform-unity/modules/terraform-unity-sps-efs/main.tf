resource "aws_kms_key" "efs_key" {
  description             = "KMS key for EFS encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "EfsKmsKey")
    Component = "airflow"
    Stack     = "airflow"
  })
}

resource "aws_kms_alias" "efs_key_alias" {
  name          = "alias/${format(local.resource_name_prefix, "efs-key")}"
  target_key_id = aws_kms_key.efs_key.key_id
}

resource "aws_efs_file_system" "efs" {
  creation_token = format(local.resource_name_prefix, "AirflowEfs")
  encrypted      = true
  kms_key_id     = aws_kms_key.efs_key.arn

  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "AirflowEfs")
    Component = "airflow"
    Stack     = "airflow"
  })
}
