# S3 bucket for static website hosting (private, accessed via CloudFront)
resource "aws_s3_bucket" "static_site" {
  bucket = "${var.project}-${var.environment}-static-site"
}

# Upload sample HTML file
resource "aws_s3_object" "index_html" {
  bucket = aws_s3_bucket.static_site.id
  key    = "index.html"
  content = templatefile("${path.module}/sample-site/index.html", {
    project_name = var.project
    environment  = var.environment
  })
  content_type = "text/html"
}

resource "aws_s3_object" "error_html" {
  bucket = aws_s3_bucket.static_site.id
  key    = "error.html"
  content = templatefile("${path.module}/sample-site/error.html", {
    project_name = var.project
    environment  = var.environment
  })
  content_type = "text/html"
}

# Output the S3 bucket name for deployment
output "s3_bucket_name" {
  description = "Name of the S3 bucket for deployment"
  value       = aws_s3_bucket.static_site.bucket
}
