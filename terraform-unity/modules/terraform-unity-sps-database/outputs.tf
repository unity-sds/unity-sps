output "db_instance_identifier" {
  value = aws_db_instance.sps_db.id
}

output "db_secret_arn" {
  value = aws_secretsmanager_secret_version.db.arn
}

output "db_latest_snapshot" {
  value = data.aws_db_snapshot.latest_snapshot[0].db_snapshot_arn
}
