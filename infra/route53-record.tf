# Route53 record to point lit-up.kevinmccartney.is to CloudFront
resource "aws_route53_record" "lit_up_domain" {
  zone_id = data.aws_route53_zone.kevinmccartney_is.zone_id
  name    = "lit-up.kevinmccartney.is"
  type    = "CNAME"
  records = [aws_cloudfront_distribution.static_site.domain_name]
  ttl     = 300

  # alias {
  #   name                   = aws_cloudfront_distribution.static_site.domain_name
  #   zone_id                = aws_cloudfront_distribution.static_site.hosted_zone_id
  #   evaluate_target_health = false
  # }
}
