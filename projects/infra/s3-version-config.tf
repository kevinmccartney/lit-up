# S3 bucket for manually uploaded per-version config files (private)
#
# Intended use:
# - Upload files like: s3://<bucket>/v1/config.json, s3://<bucket>/v5/config.json
# - Keep version-specific, operator-managed config separate from the static site bucket.
resource "aws_s3_bucket" "version_config" {
  bucket = "${var.project}-${var.environment}-version-config"

  tags = {
    Name        = "${var.project}-${var.environment}-version-config"
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_s3_bucket_public_access_block" "version_config" {
  bucket = aws_s3_bucket.version_config.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "version_config" {
  bucket = aws_s3_bucket.version_config.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Optional: keep a small safety net against accidental deletes
resource "aws_s3_bucket_versioning" "version_config" {
  bucket = aws_s3_bucket.version_config.id
  versioning_configuration {
    status = "Enabled"
  }
}

output "version_config_bucket_name" {
  description = "S3 bucket name for manually uploaded per-version config files"
  value       = aws_s3_bucket.version_config.bucket
}

output "version_config_bucket_arn" {
  description = "ARN of the version config bucket"
  value       = aws_s3_bucket.version_config.arn
}


