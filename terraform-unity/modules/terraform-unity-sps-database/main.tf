resource "random_password" "db" {
  length           = 16
  special          = true
  override_special = "_!%^"
}

resource "aws_secretsmanager_secret" "db" {
  name                    = format(local.resource_name_prefix, "db")
  recovery_window_in_days = 0
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "db")
    Component = "processing"
    Stack     = "processing"
  })
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id     = aws_secretsmanager_secret.db.id
  secret_string = random_password.db.result
}

resource "aws_db_subnet_group" "db" {
  name       = format(local.resource_name_prefix, "db")
  subnet_ids = jsondecode(data.aws_ssm_parameter.subnet_ids.value)["private"]
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "db")
    Component = "processing"
    Stack     = "processing"
  })
}

# Security group for RDS
resource "aws_security_group" "rds_sg" {
  name        = format(local.resource_name_prefix, "RdsEc2")
  description = "Security group for RDS instance to allow traffic from EKS nodes"
  vpc_id      = data.aws_eks_cluster.cluster.vpc_config[0].vpc_id
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "RdsEc2")
    Component = "airflow"
    Stack     = "airflow"
  })
}

# Ingress rule for RDS security group to allow PostgreSQL traffic from EKS nodes security group
resource "aws_security_group_rule" "rds_ingress_from_eks" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.rds_sg.id
  source_security_group_id = data.aws_security_group.default.id
}

# Egress rule for EKS nodes security group to allow PostgreSQL traffic to RDS security group
resource "aws_security_group_rule" "eks_egress_to_rds" {
  type                     = "egress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = data.aws_security_group.default.id
  source_security_group_id = aws_security_group.rds_sg.id
}


resource "aws_db_instance" "sps_db" {
  identifier           = format(local.resource_name_prefix, "db")
  allocated_storage    = 100
  storage_type         = "gp3"
  engine               = "postgres"
  engine_version       = "16.4"
  instance_class       = "db.m5d.large"
  db_name              = "sps_db"
  username             = "db_user"
  password             = aws_secretsmanager_secret_version.db.secret_string
  parameter_group_name = "default.postgres16"

  backup_retention_period = 7
  backup_window           = "01:00-02:00"
  storage_encrypted       = true
  copy_tags_to_snapshot   = true

  skip_final_snapshot       = false
  final_snapshot_identifier = "${terraform.workspace}-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  snapshot_identifier       = try(data.aws_db_snapshot.latest_snapshot[0].id, null)
  publicly_accessible       = false
  db_subnet_group_name      = aws_db_subnet_group.db.name
  vpc_security_group_ids    = [aws_security_group.rds_sg.id]
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "db")
    Component = "processing"
    Stack     = "processing"
  })

  lifecycle {
    ignore_changes = [
      snapshot_identifier,
      final_snapshot_identifier
    ]
  }
}
