variable "rule_name" {
  description = "Name of the EventBridge rule."
  type        = string
}

variable "description" {
  description = "Description of the EventBridge rule."
  type        = string
  default     = "EventBridge scheduled rule"
}

variable "schedule_expression" {
  description = "Schedule expression (cron or rate)."
  type        = string
}

variable "target_arn" {
  description = "ARN of the target resource to invoke."
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function for invoke permission."
  type        = string
}

variable "target_input" {
  description = "JSON input payload string for the target."
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to assign to resources."
  type        = map(string)
  default     = {}
}
