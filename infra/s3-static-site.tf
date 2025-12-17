# S3 bucket for static website hosting (private, accessed via CloudFront)
resource "aws_s3_bucket" "static_site" {
  bucket = "${var.project}-${var.environment}-static-site"
}

# Output the S3 bucket name for deployment
output "s3_bucket_name" {
  description = "Name of the S3 bucket for deployment"
  value       = aws_s3_bucket.static_site.bucket
}

# Output the CloudFront distribution URL
output "cloudfront_url" {
  description = "CloudFront distribution URL"
  value       = "https://${aws_cloudfront_distribution.static_site.domain_name}"
}
