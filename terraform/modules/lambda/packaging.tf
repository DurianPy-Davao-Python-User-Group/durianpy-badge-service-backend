locals {
  top_level_items = length(var.include_patterns) > 0 ? fileset(var.source_dir, "*") : []
  implicit_excludes = [
    for item in local.top_level_items : item
    if !contains(var.include_patterns, item) && !contains(var.include_patterns, split("/", item)[0])
  ]
  effective_excludes = distinct(concat(var.exclude_patterns, local.implicit_excludes))
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${path.module}/.build/${var.function_name}.zip"
  excludes    = local.effective_excludes
}

resource "terraform_data" "lambda_layer" {
  count = var.enable_lambda_layer ? 1 : 0

  triggers_replace = [
    filesha256("${var.source_dir}/pyproject.toml"),
    fileexists("${var.source_dir}/uv.lock") ? filesha256("${var.source_dir}/uv.lock") : ""
  ]

  provisioner "local-exec" {
    command = "bash ${path.module}/scripts/build_layer.sh '${var.source_dir}' '${path.module}/.build' '${var.runtime}' '${join(",", var.architectures)}'"
  }
}

data "archive_file" "lambda_layer_zip" {
  count       = var.enable_lambda_layer ? 1 : 0
  type        = "zip"
  source_dir  = "${path.module}/.build/layer"
  output_path = "${path.module}/.build/${var.function_name}-layer.zip"

  depends_on = [
    terraform_data.lambda_layer
  ]
}

resource "aws_lambda_layer_version" "dependencies" {
  count                    = var.enable_lambda_layer ? 1 : 0
  layer_name               = "${var.function_name}-dependencies"
  description              = "Dependencies layer for ${var.function_name} generated from pyproject.toml"
  filename                 = data.archive_file.lambda_layer_zip[0].output_path
  source_code_hash         = data.archive_file.lambda_layer_zip[0].output_base64sha256
  compatible_runtimes      = [var.runtime]
  compatible_architectures = var.architectures
}
