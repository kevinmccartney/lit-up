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
