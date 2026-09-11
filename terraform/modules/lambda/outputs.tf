output "function_arn" {
  description = "The ARN of the Lambda function."
  value       = aws_lambda_function.function.arn
}

output "function_name" {
  description = "The name of the Lambda function."
  value       = aws_lambda_function.function.function_name
}

output "invoke_arn" {
  description = "The invocation ARN of the Lambda function."
  value       = aws_lambda_function.function.invoke_arn
}

output "role_arn" {
  description = "The ARN of the IAM role attached to the Lambda function."
  value       = local.role_arn
}

output "role_name" {
  description = "The name of the IAM role attached to the Lambda function."
  value       = local.role_name
}

output "log_group_name" {
  description = "The name of the CloudWatch Log Group for the Lambda function."
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "log_group_arn" {
  description = "The ARN of the CloudWatch Log Group for the Lambda function."
  value       = aws_cloudwatch_log_group.lambda_logs.arn
}

output "layer_arn" {
  description = "The ARN of the Lambda dependencies layer version (if enabled)."
  value       = var.enable_lambda_layer ? aws_lambda_layer_version.dependencies[0].arn : null
}

output "layer_version" {
  description = "The version number of the Lambda dependencies layer (if enabled)."
  value       = var.enable_lambda_layer ? aws_lambda_layer_version.dependencies[0].version : null
}
