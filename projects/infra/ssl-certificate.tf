# SSL Certificate for lit-up.kevinmccartney.is
resource "aws_acm_certificate" "lit_up_cert" {
  domain_name       = "lit-up.kevinmccartney.is"
  validation_method = "DNS"

  # Optional: Add Subject Alternative Names (SANs)
  subject_alternative_names = []

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "${var.project}-${var.environment}-ssl-cert"
    Environment = var.environment
    Project     = var.project
  }
}

# DNS validation records for the certificate
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.lit_up_cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.kevinmccartney_is.zone_id
}

# Certificate validation
resource "aws_acm_certificate_validation" "lit_up_cert_validation" {
  certificate_arn         = aws_acm_certificate.lit_up_cert.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]

  timeouts {
    create = "5m"
  }
}

# Data source to get the Route53 zone for kevinmccartney.is
data "aws_route53_zone" "kevinmccartney_is" {
  name         = "kevinmccartney.is"
  private_zone = false
}

# Outputs
output "certificate_arn" {
  description = "ARN of the SSL certificate"
  value       = aws_acm_certificate.lit_up_cert.arn
}

output "certificate_domain_name" {
  description = "Domain name of the SSL certificate"
  value       = aws_acm_certificate.lit_up_cert.domain_name
}

# output "certificate_validation_status" {
#   description = "Validation status of the SSL certificate"
#   value       = aws_acm_certificate_validation.lit_up_cert_validation.certificate_arn
# }
