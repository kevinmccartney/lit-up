resource "aws_ssm_parameter" "auth_username" {
  name        = "/${var.project}/${var.environment}/auth/username"
  description = "Basic auth username for ${var.project} (${var.environment})"
  type        = "String"
  value       = var.auth_username
  overwrite   = true

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "auth_password" {
  name        = "/${var.project}/${var.environment}/auth/password"
  description = "Basic auth password for ${var.project} (${var.environment})"
  type        = "SecureString"
  value       = var.auth_password
  overwrite   = true

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "active_versions" {
  name        = "/${var.project}/${var.environment}/active_versions"
  description = "Comma-delimited list of active app versions, e.g. v1,v5"
  type        = "String"
  value       = var.ACTIVE_VERSIONS
  overwrite   = true

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}


