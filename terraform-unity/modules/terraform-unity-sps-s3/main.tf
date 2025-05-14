# Create an S3 bucket to use as Kubernetes Persistent Volume
resource "aws_s3_bucket" "s3_pv_bucket" {
  bucket        = format(local.resource_name_prefix, "s3-pv")
  force_destroy = true
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "s3-pv")
    Component = "airflow"
    Stack     = "airflow"
  })
}

resource "aws_s3_bucket_policy" "s3_pv_bucket_policy" {
  bucket = aws_s3_bucket.s3_pv_bucket.id
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
            format("%s%s", "arn:aws:s3:::", format(local.resource_name_prefix, "s3-pv")),
            format("%s%s/%s", "arn:aws:s3:::", format(local.resource_name_prefix, "s3-pv"), "*")
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

# Store the bucket name as SSM parameter
# Example: /luca-1/dev/sps/processing/airflow/s3_pv
resource "aws_ssm_parameter" "s3_pv_bucket_ssm_parameter" {
  name        = format("/%s", join("/", compact(["", var.project, var.venue, var.service_area, "processing", "airflow", "s3_pv"])))
  description = "The name of the S3 bucket for the S3 Persistent Volume"
  type        = "String"
  value       = aws_s3_bucket.s3_pv_bucket.id
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "S3-PV")
    Component = "SSM"
    Stack     = "SSM"
  })
}

# Install the CSI S3 driver via Helm
resource "helm_release" "csi_s3" {
  name      = "csi-driver-s3"
  namespace = var.kubernetes_namespace

  repository = "https://awslabs.github.io/mountpoint-s3-csi-driver/"
  chart      = "aws-mountpoint-s3-csi-driver"
  # Check for latest at the repo if needed
  version = "1.14.1"

  set {
    name  = "s3.endpoint"
    value = "https://s3.amazonaws.com"
  }

  set {
    name  = "s3.region"
    value = var.aws_region
  }
}

# Create a StorageClass for S3
resource "kubernetes_storage_class" "s3" {
  metadata {
    name = "s3-sc"
  }

  storage_provisioner = "s3.csi.aws.com"

  parameters = {
    mounter = "s3fs"
    bucket  = aws_s3_bucket.s3_pv_bucket.id
    region  = var.aws_region

  }

  # "Delete" or "Retain"?
  reclaim_policy      = "Delete"
  volume_binding_mode = "Immediate"
}

# Create a PersistentVolume
resource "kubernetes_persistent_volume" "s3_pv" {
  metadata {
    name = "s3-pv"
  }

  spec {
    capacity = {
      # Required but irrelevant for S3
      storage = "100Gi"
    }

    access_modes                     = ["ReadWriteMany"]
    persistent_volume_reclaim_policy = "Delete"
    storage_class_name               = kubernetes_storage_class.s3.metadata[0].name
    persistent_volume_source {
      csi {
        driver = "s3.csi.aws.com"
        # must be universally unique
        volume_handle = "${aws_s3_bucket.s3_pv_bucket.id}-handle"

        volume_attributes = {
          bucketName = aws_s3_bucket.s3_pv_bucket.id
          mounter    = "s3fs"
        }
      }
    }
  }
}

# 4. Create a PersistentVolumeClaim
resource "kubernetes_persistent_volume_claim" "s3_pvc" {
  metadata {
    name      = "s3-pvc"
    namespace = var.kubernetes_namespace
  }

  spec {
    access_modes = ["ReadWriteMany"]

    resources {
      requests = {
        storage = "100Gi"
      }
    }

    storage_class_name = "s3-sc"
    volume_name        = kubernetes_persistent_volume.s3_pv.metadata[0].name
  }
}
