output "api_id" {
  description = "The ID of the API Gateway HTTP API."
  value       = aws_apigatewayv2_api.api.id
}

output "api_endpoint" {
  description = "The default URL endpoint of the API Gateway HTTP API."
  value       = aws_apigatewayv2_api.api.api_endpoint
}

output "api_arn" {
  description = "The ARN of the API Gateway HTTP API."
  value       = aws_apigatewayv2_api.api.arn
}

output "execution_arn" {
  description = "The execution ARN of the API Gateway HTTP API."
  value       = aws_apigatewayv2_api.api.execution_arn
}

output "stage_id" {
  description = "The ID of the deployment stage."
  value       = aws_apigatewayv2_stage.stage.id
}

output "access_log_group_name" {
  description = "The name of the CloudWatch Log Group for API Gateway access logs."
  value       = aws_cloudwatch_log_group.api_access_logs.name
}
