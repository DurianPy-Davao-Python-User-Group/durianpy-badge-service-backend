variable "aws_region" {
  description = "AWS region for provisioning resources."
  type        = string
  default     = "ap-southeast-1"
}

variable "environment" {
  description = "Target deployment environment ('dev', 'prod')."
  type        = string
  default     = "dev"
}

variable "app_name" {
  description = "Application name prefix for resource naming."
  type        = string
  default     = "durianpy-badge-system"
}

variable "enable_basic_auth" {
  description = "Enable Basic Auth on API Gateway for securing /docs."
  type        = bool
  default     = true
}

variable "basic_auth_username" {
  description = "Basic Auth username for securing dev endpoints."
  type        = string
  default     = "admin"
}

variable "basic_auth_password" {
  description = "Basic Auth password for securing dev endpoints."
  type        = string
  default     = ""
  sensitive   = true
}
