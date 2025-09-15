# CloudFront distribution with Lambda@Edge authentication
resource "aws_cloudfront_distribution" "static_site" {
  origin {
    domain_name = aws_s3_bucket.static_site.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.static_site.bucket}"

    origin_access_control_id = aws_cloudfront_origin_access_control.static_site.id
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  # Custom error pages for SPA routing
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.static_site.bucket}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    # Lambda@Edge for authentication
    lambda_function_association {
      event_type   = "viewer-request"
      lambda_arn   = aws_lambda_function.auth_function.qualified_arn
      include_body = false
    }

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  # Custom domain configuration
  aliases = ["lit-up.kevinmccartney.is"]

  # SSL certificate configuration
  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.lit_up_cert_validation.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  # Price class for cost optimization
  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # viewer_certificate {
  #   cloudfront_default_certificate = true
  # }

  tags = {
    Name        = "${var.project}-${var.environment}-static-site"
    Environment = var.environment
  }

  depends_on = [
    aws_lambda_permission.allow_cloudfront,
    # aws_s3_bucket_policy.static_site_cloudfront
  ]
}

# Origin Access Control for CloudFront to access S3
resource "aws_cloudfront_origin_access_control" "static_site" {
  name                              = "${var.project}-${var.environment}-oac"
  description                       = "OAC for ${var.project} static site"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# Lambda function for authentication
resource "aws_lambda_function" "auth_function" {
  filename         = "lambda-auth.zip"
  function_name    = "${var.project}-${var.environment}-auth"
  role             = aws_iam_role.lambda_edge_role.arn
  handler          = "index.handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "nodejs18.x"
  publish          = true

  # Note: Lambda@Edge doesn't support environment variables
  # Credentials are embedded via templatefile() in the source code

  tags = {
    Name        = "${var.project}-${var.environment}-auth"
    Environment = var.environment
  }
}

# Lambda deployment package
data "archive_file" "lambda_zip" {
  type        = "zip"
  output_path = "lambda-auth.zip"
  source {
    content = templatefile("${path.module}/lambda-auth/index.js", {
      auth_username = var.auth_username
      auth_password = var.auth_password
    })
    filename = "index.js"
  }
}

# IAM role for Lambda@Edge
resource "aws_iam_role" "lambda_edge_role" {
  name = "${var.project}-${var.environment}-lambda-edge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "lambda.amazonaws.com",
            "edgelambda.amazonaws.com"
          ]
        }
      }
    ]
  })
}

# IAM policy for Lambda@Edge
resource "aws_iam_role_policy_attachment" "lambda_edge_policy" {
  role       = aws_iam_role.lambda_edge_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Permission for CloudFront to invoke Lambda
resource "aws_lambda_permission" "allow_cloudfront" {
  statement_id  = "AllowExecutionFromCloudFront"
  action        = "lambda:GetFunction"
  function_name = aws_lambda_function.auth_function.function_name
  principal     = "edgelambda.amazonaws.com"
}

# Update S3 bucket policy for CloudFront access
resource "aws_s3_bucket_policy" "static_site_cloudfront" {
  bucket = aws_s3_bucket.static_site.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.static_site.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.static_site.arn
          }
        }
      }
    ]
  })

  depends_on = [aws_cloudfront_distribution.static_site]
}

# Remove public access block since we're using CloudFront
resource "aws_s3_bucket_public_access_block" "static_site_private" {
  bucket = aws_s3_bucket.static_site.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Remove the old public bucket policy
resource "aws_s3_bucket_policy" "static_site_public" {
  count  = 0 # Disable the old public policy
  bucket = aws_s3_bucket.static_site.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.static_site.arn}/*"
      }
    ]
  })
}

# Outputs
output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.static_site.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.static_site.id
}

output "website_url" {
  description = "URL of the password-protected static website"
  value       = "https://${aws_cloudfront_distribution.static_site.domain_name}"
}
