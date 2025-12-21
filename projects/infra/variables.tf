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

variable "active_versions" {
  description = "Comma-delimited list of existing versions, e.g. 'v1,v2,v3'"
  type        = string
  default     = "v1,v2"
}

variable "api_allowed_source_cidrs" {
  description = "List of CIDRs allowed to invoke the REST API Gateway (resource policy). Example: [\"203.0.113.10/32\"]"
  type        = list(string)
  default     = []
}
