output "api_endpoint" {
  description = "The public base URL of the API Gateway HTTP API."
  value       = module.apigw.api_endpoint
}

output "api_id" {
  description = "The ID of the API Gateway."
  value       = module.apigw.api_id
}

output "lambda_function_arn" {
  description = "The ARN of the backend Lambda function."
  value       = module.lambda.function_arn
}

output "lambda_function_name" {
  description = "The name of the backend Lambda function."
  value       = module.lambda.function_name
}

output "lambda_role_arn" {
  description = "The ARN of the Lambda execution IAM role."
  value       = module.lambda.role_arn
}

output "lambda_layer_arn" {
  description = "The ARN of the Lambda dependencies layer (if enabled)."
  value       = module.lambda.layer_arn
}

output "warmer_rule_arn" {
  description = "The ARN of the EventBridge warmer rule (if enabled)."
  value       = local.warmer_configuration.enabled ? module.event_bridge_warmer[0].rule_arn : null
}
