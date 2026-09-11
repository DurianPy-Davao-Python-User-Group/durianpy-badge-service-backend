variable "api_name" {
  description = "Name of the API Gateway HTTP API."
  type        = string
}

variable "description" {
  description = "Description of the API Gateway HTTP API."
  type        = string
  default     = "HTTP API Gateway provisioned with Terraform"
}

variable "lambda_arn" {
  description = "ARN (or invoke ARN) of the backend Lambda function to integrate."
  type        = string
}

variable "lambda_name" {
  description = "Name of the backend Lambda function."
  type        = string
}

variable "stage_name" {
  description = "Name of the deployment stage."
  type        = string
  default     = "$default"
}

variable "auto_deploy" {
  description = "Whether to automatically deploy stage updates."
  type        = bool
  default     = true
}

variable "log_retention_in_days" {
  description = "CloudWatch log retention in days for API Gateway access logs."
  type        = number
  default     = 30
}

variable "enable_throttling" {
  description = "Enable request rate and burst throttling on API Gateway (disabled by default)."
  type        = bool
  default     = false
}

variable "throttling_rate_limit" {
  description = "Throttling rate limit (average requests per second)."
  type        = number
  default     = 100
}

variable "throttling_burst_limit" {
  description = "Throttling burst limit (maximum burst requests)."
  type        = number
  default     = 200
}

variable "cors_allow_origins" {
  description = "Allowed origins for CORS."
  type        = list(string)
  default     = ["*"]
}

variable "cors_allow_methods" {
  description = "Allowed HTTP methods for CORS."
  type        = list(string)
  default     = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
}

variable "cors_allow_headers" {
  description = "Allowed HTTP headers for CORS."
  type        = list(string)
  default     = ["Content-Type", "Authorization", "X-Amz-Date", "X-Api-Key", "X-Amz-Security-Token"]
}

variable "cors_max_age" {
  description = "Maximum age (in seconds) that browser may cache CORS preflight response."
  type        = number
  default     = 300
}

variable "tags" {
  description = "A mapping of tags to assign to the resources."
  type        = map(string)
  default     = {}
}
