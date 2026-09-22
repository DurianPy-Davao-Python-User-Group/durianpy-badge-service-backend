provider "aws" {
  region = var.aws_region
}

data "aws_ssm_parameter" "cloudfront_url" {
  name = "/durianpy-badge-system/backend/cloudfront-url-${var.environment}"
}

data "aws_ssm_parameter" "swagger_basic_auth_username" {
  count           = var.enable_basic_auth ? 1 : 0
  name            = "/durianpy-badge-system/backend/swagger-basic-auth-username-${var.environment}"
  with_decryption = true
}

data "aws_ssm_parameter" "swagger_basic_auth_password" {
  count           = var.enable_basic_auth ? 1 : 0
  name            = "/durianpy-badge-system/backend/swagger-basic-auth-password-${var.environment}"
  with_decryption = true
}

locals {
  application_name = var.app_name
  environment      = var.environment
  aws_region       = var.aws_region
  service_name     = "${local.environment}-${local.application_name}"

  environment_settings = {
    "dev" = {
      warmer_concurrency = 1
    }
    # "prod" = {
    #   warmer_concurrency = 2
    # }
  }

  current_environment_settings = lookup(
    local.environment_settings,
    local.environment,
    {
      warmer_concurrency = 1
    }
  )

  warmer_configuration = {
    concurrency         = local.current_environment_settings.warmer_concurrency
    schedule_expression = "cron(0/10 * ? * * *)"
    enabled             = local.current_environment_settings.warmer_concurrency > 0
  }

  environment_variables = {
    APP_NAME                    = local.application_name
    ENVIRONMENT                 = local.environment
    LOG_LEVEL                   = local.environment == "prod" ? "info" : "debug"
    REGION                      = local.aws_region
    CLOUDFRONT_URL              = data.aws_ssm_parameter.cloudfront_url.value
    DYNAMODB_MAIN_TABLE_NAME    = "${local.environment}-${local.application_name}-main"
    ENABLE_SWAGGER_BASIC_AUTH   = local.enable_basic_auth ? "true" : "false"
    SWAGGER_BASIC_AUTH_USERNAME = local.basic_auth_username
    SWAGGER_BASIC_AUTH_PASSWORD = local.basic_auth_password
  }

  enable_basic_auth   = var.enable_basic_auth
  basic_auth_username = var.enable_basic_auth ? data.aws_ssm_parameter.swagger_basic_auth_username[0].value : var.basic_auth_username
  basic_auth_password = var.enable_basic_auth ? data.aws_ssm_parameter.swagger_basic_auth_password[0].value : var.basic_auth_password

  lambda_policy_statements = [
    {
      effect = "Allow"
      actions = [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ]
      resources = [
        "arn:aws:ssm:${local.aws_region}:*:parameter/durianpy-badge-system/backend/*"
      ]
    },
    {
      effect = "Allow"
      actions = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:BatchGetItem",
        "dynamodb:BatchWriteItem",
        "dynamodb:ConditionCheckItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ]
      resources = [
        "arn:aws:dynamodb:${local.aws_region}:*:table/${local.environment}-${local.application_name}-*",
        "arn:aws:dynamodb:${local.aws_region}:*:table/${local.environment}-${local.application_name}-*/index/*"
      ]
    },
    {
      effect = "Allow"
      actions = [
        "lambda:InvokeFunction"
      ]
      resources = [
        "arn:aws:lambda:${local.aws_region}:*:function:${local.service_name}-api*"
      ]
    }
  ]

  tags = {
    Application = local.application_name
    Environment = local.environment
    ManagedBy   = "Terraform"
  }
}

module "lambda" {
  source = "./modules/lambda"

  function_name = "${local.service_name}-api"
  description   = "FastAPI & Mangum backend for ${local.application_name} (${local.environment})"
  runtime       = "python3.12"
  architectures = ["x86_64"]
  memory_size   = 256
  timeout       = 29

  handler    = "src.presentation.api.mangum_handler.handler"
  source_dir = "${path.module}/.."

  include_patterns = [
    "src",
  ]

  exclude_patterns = [
    ".git/**",
    ".github/**",
    ".venv/**",
    ".pytest_cache/**",
    ".ruff_cache/**",
    "tests/**",
    "terraform/**",
    "**/__pycache__/**",
    "**/*.pyc",
    "**/*.pyo",
    "**/.DS_Store",
    "**/docker/**",
    "**/.devcontainer/**",
    "**/modules/**"
  ]

  environment_variables = local.environment_variables
  policy_statements     = local.lambda_policy_statements
  policy_arns           = []

  log_retention_in_days = 14
  enable_tracing        = false

  tags = local.tags
}

module "apigw" {
  source = "./modules/apigw"

  api_name    = "${local.service_name}-http-api"
  description = "HTTP API Gateway proxying requests to ${module.lambda.function_name}"
  lambda_arn  = module.lambda.invoke_arn
  lambda_name = module.lambda.function_name
  stage_name  = "$default"
  auto_deploy = true

  enable_throttling      = false
  throttling_rate_limit  = 100
  throttling_burst_limit = 200
  log_retention_in_days  = 30

  cors_allow_origins = ["*"]
  cors_allow_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
  cors_allow_headers = ["Content-Type", "Authorization", "X-Amz-Date", "X-Api-Key", "X-Amz-Security-Token"]

  tags = local.tags
}

module "event_bridge_warmer" {
  count  = local.warmer_configuration.enabled ? 1 : 0
  source = "./modules/event-bridge"

  rule_name            = "${local.service_name}-warmer"
  description          = "EventBridge scheduled rule for Lambda warmer"
  schedule_expression  = local.warmer_configuration.schedule_expression
  target_arn           = module.lambda.function_arn
  lambda_function_name = module.lambda.function_name
  target_input = jsonencode({
    warmer      = true
    concurrency = local.warmer_configuration.concurrency
  })

  tags = local.tags
}
