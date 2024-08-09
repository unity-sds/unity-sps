output "db_instance_identifier" {
  value = aws_db_instance.sps_db.id
}

output "db_secret_version" {
  value = aws_secretsmanager_secret_version.db.version_id
}
