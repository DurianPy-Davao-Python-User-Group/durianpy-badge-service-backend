locals {
  create_role = var.role_arn == null
  role_arn    = local.create_role ? aws_iam_role.lambda_exec[0].arn : var.role_arn
  role_name   = local.create_role ? aws_iam_role.lambda_exec[0].name : null
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_in_days
  tags              = var.tags
}

resource "aws_iam_role" "lambda_exec" {
  count = local.create_role ? 1 : 0
  name  = "${var.function_name}-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_policy" "lambda_logging" {
  count       = local.create_role ? 1 : 0
  name        = "${var.function_name}-logging-policy"
  description = "IAM policy for Lambda function logging strictly to its dedicated CloudWatch log group"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.lambda_logs.arn}:*"
        ]
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  count      = local.create_role ? 1 : 0
  role       = local.role_name
  policy_arn = aws_iam_policy.lambda_logging[0].arn
}

resource "aws_iam_role_policy_attachment" "lambda_xray" {
  count      = local.create_role && var.enable_tracing ? 1 : 0
  role       = local.role_name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

resource "aws_iam_policy" "custom" {
  count       = local.create_role && length(var.policy_statements) > 0 ? 1 : 0
  name        = "${var.function_name}-custom-policy"
  description = "Custom IAM permissions policy for ${var.function_name}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      for s in var.policy_statements : {
        Effect   = lookup(s, "effect", lookup(s, "Effect", "Allow"))
        Action   = lookup(s, "actions", lookup(s, "Action", null))
        Resource = lookup(s, "resources", lookup(s, "Resource", null))
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "custom" {
  count      = local.create_role && length(var.policy_statements) > 0 ? 1 : 0
  role       = local.role_name
  policy_arn = aws_iam_policy.custom[0].arn
}

resource "aws_iam_role_policy_attachment" "additional" {
  for_each   = local.create_role ? toset(var.policy_arns) : []
  role       = local.role_name
  policy_arn = each.value
}

resource "aws_lambda_function" "function" {
  function_name    = var.function_name
  description      = var.description
  role             = local.role_arn
  handler          = var.handler
  runtime          = var.runtime
  architectures    = var.architectures
  memory_size      = var.memory_size
  timeout          = var.timeout
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  layers = concat(
    var.layers,
    var.enable_lambda_layer ? [aws_lambda_layer_version.dependencies[0].arn] : []
  )

  tracing_config {
    mode = var.enable_tracing ? "Active" : "PassThrough"
  }

  dynamic "environment" {
    for_each = length(var.environment_variables) > 0 ? [1] : []
    content {
      variables = var.environment_variables
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs
  ]

  tags = var.tags
}
