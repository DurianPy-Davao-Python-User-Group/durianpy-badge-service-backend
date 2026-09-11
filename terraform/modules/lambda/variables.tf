variable "function_name" {
  description = "Name of the Lambda function."
  type        = string
}

variable "description" {
  description = "Description of the Lambda function."
  type        = string
  default     = "AWS Lambda function managed by Terraform"
}

variable "handler" {
  description = "Lambda function handler entrypoint (e.g. 'src.presentation.api.mangum_handler.handler')."
  type        = string
}

variable "runtime" {
  description = "Lambda execution runtime."
  type        = string
  default     = "python3.12"
}

variable "architectures" {
  description = "Instruction set architecture for the Lambda function ('x86_64' or 'arm64')."
  type        = list(string)
  default     = ["x86_64"]
}

variable "memory_size" {
  description = "Amount of memory in MB allocated to the Lambda function."
  type        = number
  default     = 256
}

variable "timeout" {
  description = "Execution timeout in seconds for the Lambda function."
  type        = number
  default     = 30
}

variable "source_dir" {
  description = "Path to the root source directory to package."
  type        = string
}

variable "include_patterns" {
  description = "List of files or directories to include relative to source_dir. If empty, all files in source_dir are included."
  type        = list(string)
  default     = []
}

variable "exclude_patterns" {
  description = "List of files, directories, or glob patterns to exclude from packaging."
  type        = list(string)
  default = [
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
  ]
}

variable "environment_variables" {
  description = "Environment variables for the Lambda function."
  type        = map(string)
  default     = {}
}

variable "log_retention_in_days" {
  description = "CloudWatch log retention in days for Lambda logs."
  type        = number
  default     = 30
}

variable "enable_tracing" {
  description = "Enable AWS X-Ray active tracing on the Lambda function (disabled by default)."
  type        = bool
  default     = false
}

variable "tags" {
  description = "A mapping of tags to assign to the resources."
  type        = map(string)
  default     = {}
}

variable "role_arn" {
  description = "Optional existing IAM role ARN to use for Lambda execution. If null, a role with least-privilege logging is created."
  type        = string
  default     = null
}

variable "policy_statements" {
  description = "List of IAM policy statement maps defining custom permissions (actions, resources, and optional effect)."
  type        = any
  default     = []
}

variable "policy_arns" {
  description = "List of existing IAM policy ARNs to attach to the Lambda execution role."
  type        = list(string)
  default     = []
}

variable "enable_lambda_layer" {
  description = "Whether to create and attach a Lambda layer with dependencies generated from pyproject.toml."
  type        = bool
  default     = true
}

variable "layers" {
  description = "List of additional Lambda Layer ARNs to attach to the Lambda function."
  type        = list(string)
  default     = []
}
