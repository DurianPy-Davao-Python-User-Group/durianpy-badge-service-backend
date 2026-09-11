resource "aws_cloudwatch_event_rule" "warmer" {
  name                = var.rule_name
  description         = var.description
  schedule_expression = var.schedule_expression
  tags                = var.tags
}

resource "aws_cloudwatch_event_target" "warmer" {
  rule      = aws_cloudwatch_event_rule.warmer.name
  target_id = "${var.rule_name}-target"
  arn       = var.target_arn
  input     = var.target_input
}

resource "aws_lambda_permission" "warmer" {
  statement_id  = "AllowExecutionFromEventBridge-${var.rule_name}"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.warmer.arn
}
