data "aws_region" "current" {}

data "aws_eks_cluster" "cluster" {
  name = format(local.resource_name_prefix, "eks")
}

data "aws_ssm_parameter" "subnet_ids" {
  name = "/unity/account/network/subnet_list"
}

data "aws_security_group" "default" {
  vpc_id = data.aws_eks_cluster.cluster.vpc_config[0].vpc_id
  filter {
    name   = "tag:Name"
    values = ["${format(local.resource_name_prefix, "eks")}-node"]
  }
}

data "aws_db_snapshot" "latest_snapshot" {
  count                  = data.external.rds_final_snapshot_exists.result.db_exists ? 1 : 0
  db_instance_identifier = format(local.resource_name_prefix, "db")
  most_recent            = true

}

data "external" "rds_final_snapshot_exists" {
  program = [
    "${path.module}/check_rds_snapshot.sh",
    format(local.resource_name_prefix, "db"),
    data.aws_region.current.name
  ]
}
