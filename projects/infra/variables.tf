variable "project" {
  description = "Project identifier used for naming resources"
  type        = string
  default     = "lit-up"
}

variable "environment" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "auth_username" {
  description = "Username for basic authentication"
  type        = string
  default     = "admin"
}

variable "auth_password" {
  description = "Password for basic authentication"
  type        = string
  default     = "changeme123"
  sensitive   = true
}

variable "ACTIVE_VERSIONS" {
  description = "Comma-delimited list of existing versions, e.g. 'v1,v2,v3'"
  type        = string
  default     = "v1,v2"
}
