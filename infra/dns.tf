data "aws_route53_zone" "kevinmccartny_is" {
  name = "kevinmccartney.is"
}

resource "aws_route53_record" "lit_up" {
  zone_id = data.aws_route53_zone.kevinmccartny_is.zone_id
  name    = "lit-up.kevinmccartney.is"
  type    = "CNAME"
  ttl     = 300
  records = [aws_cloudfront_distribution.static_site.domain_name]
}
