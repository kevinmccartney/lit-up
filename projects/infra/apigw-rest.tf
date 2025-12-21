# Health check REST API Gateway -> Lambda (regional)

data "aws_region" "current" {}

resource "aws_iam_role" "lambda_execute_role" {
  name = "${var.project}-${var.environment}-lambda-execute-role"

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
}

resource "aws_iam_role_policy_attachment" "lambda_execute_basic_exec" {
  role       = aws_iam_role.lambda_execute_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "archive_file" "ping_lambda_zip" {
  type        = "zip"
  output_path = "lambda-ping.zip"
  source {
    content  = file("${path.module}/lambda-ping/index.js")
    filename = "index.js"
  }
}

resource "aws_lambda_function" "healthz_function" {
  filename         = "lambda-ping.zip"
  function_name    = "${var.project}-${var.environment}-healthz"
  role             = aws_iam_role.lambda_execute_role.arn
  handler          = "index.handler"
  source_code_hash = data.archive_file.ping_lambda_zip.output_base64sha256
  runtime          = "nodejs22.x"
  timeout          = 5
  memory_size      = 128

  tags = {
    Name        = "${var.project}-${var.environment}-healthz"
    Environment = var.environment
  }
}

# Lambda function for POST /config (Python, deployed from api project)
# Note: This Lambda is deployed independently from infra.
# The zip file should be built and uploaded separately by the api project.
# For initial setup, Terraform will create the function with a placeholder zip.
data "archive_file" "config_post_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-config-post-placeholder.zip"
  source {
    content  = "# Placeholder - Lambda code deployed separately from api project"
    filename = "placeholder.txt"
  }
}

resource "aws_lambda_function" "config_post_function" {
  filename         = data.archive_file.config_post_lambda_zip.output_path
  function_name    = "${var.project}-${var.environment}-config-post"
  role             = aws_iam_role.lambda_execute_role.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.config_post_lambda_zip.output_base64sha256
  runtime          = "python3.13"
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      CONFIG_TABLE_NAME = aws_dynamodb_table.configs.name
    }
  }

  tags = {
    Name        = "${var.project}-${var.environment}-config-post"
    Environment = var.environment
  }
}

resource "aws_api_gateway_rest_api" "lit_up_api" {
  name = "${var.project}-${var.environment}-api"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name        = "${var.project}-${var.environment}-api"
    Environment = var.environment
  }
}

# Optional IP allowlist for early-stage protection (pairs well with API keys).
# Note: Use your PUBLIC egress IP/CIDR here (not private LAN IPs like 192.168.x.x).
resource "aws_api_gateway_rest_api_policy" "lit_up_api_ip_allowlist" {
  count = length(var.api_allowed_source_cidrs) > 0 ? 1 : 0

  rest_api_id = aws_api_gateway_rest_api.lit_up_api.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowInvokeFromAllowedSourceIps"
        Effect    = "Allow"
        Principal = "*"
        Action    = "execute-api:Invoke"
        Resource  = "${aws_api_gateway_rest_api.lit_up_api.execution_arn}/*/*/*"
        Condition = {
          IpAddress = {
            "aws:SourceIp" = var.api_allowed_source_cidrs
          }
        }
      }
    ]
  })
}

resource "aws_api_gateway_resource" "healthz" {
  rest_api_id = aws_api_gateway_rest_api.lit_up_api.id
  parent_id   = aws_api_gateway_rest_api.lit_up_api.root_resource_id
  path_part   = "healthz"
}

resource "aws_api_gateway_resource" "config" {
  rest_api_id = aws_api_gateway_rest_api.lit_up_api.id
  parent_id   = aws_api_gateway_rest_api.lit_up_api.root_resource_id
  path_part   = "config"
}

resource "aws_api_gateway_method" "healthz_get" {
  rest_api_id      = aws_api_gateway_rest_api.lit_up_api.id
  resource_id      = aws_api_gateway_resource.healthz.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_method" "config_post" {
  rest_api_id      = aws_api_gateway_rest_api.lit_up_api.id
  resource_id      = aws_api_gateway_resource.config.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "healthz_get" {
  rest_api_id             = aws_api_gateway_rest_api.lit_up_api.id
  resource_id             = aws_api_gateway_resource.healthz.id
  http_method             = aws_api_gateway_method.healthz_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.healthz_function.invoke_arn
}

resource "aws_api_gateway_integration" "config_post" {
  rest_api_id             = aws_api_gateway_rest_api.lit_up_api.id
  resource_id             = aws_api_gateway_resource.config.id
  http_method             = aws_api_gateway_method.config_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.config_post_function.invoke_arn
}

resource "aws_lambda_permission" "allow_apigw_invoke_healthz" {
  statement_id  = "AllowExecutionFromApiGatewayHealthz"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.healthz_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.lit_up_api.execution_arn}/*/GET/healthz"
}

resource "aws_lambda_permission" "allow_apigw_invoke_config_post" {
  statement_id  = "AllowExecutionFromApiGatewayConfigPost"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.config_post_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.lit_up_api.execution_arn}/*/POST/config"
}

resource "aws_api_gateway_deployment" "lit_up" {
  rest_api_id = aws_api_gateway_rest_api.lit_up_api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.healthz.id,
      aws_api_gateway_method.healthz_get.id,
      aws_api_gateway_method.healthz_get.api_key_required,
      aws_api_gateway_integration.healthz_get.id,
      aws_api_gateway_resource.config.id,
      aws_api_gateway_method.config_post.id,
      aws_api_gateway_method.config_post.api_key_required,
      aws_api_gateway_integration.config_post.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "lit_up" {
  rest_api_id   = aws_api_gateway_rest_api.lit_up_api.id
  deployment_id = aws_api_gateway_deployment.lit_up.id
  stage_name    = var.environment

  tags = {
    Name        = "${var.project}-${var.environment}-api"
    Environment = var.environment
  }
}

# API key + usage plan (simple shared-secret access for local/CI callers)
resource "aws_api_gateway_api_key" "default" {
  name        = "${var.project}-${var.environment}-api-key"
  enabled     = true
  description = "API key for ${var.project} (${var.environment}) REST API"
}

resource "aws_api_gateway_usage_plan" "default" {
  name = "${var.project}-${var.environment}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.lit_up_api.id
    stage  = aws_api_gateway_stage.lit_up.stage_name
  }

  throttle_settings {
    burst_limit = 10
    rate_limit  = 5
  }
}

resource "aws_api_gateway_usage_plan_key" "default" {
  key_id        = aws_api_gateway_api_key.default.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.default.id
}

output "lit_up_api_invoke_url" {
  description = "Invoke URL for GET /healthz"
  value       = "https://${aws_api_gateway_rest_api.lit_up_api.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${aws_api_gateway_stage.lit_up.stage_name}/healthz"
}

output "lit_up_api_key_value" {
  description = "API key value to use as the x-api-key header when calling the REST API"
  value       = aws_api_gateway_api_key.default.value
  sensitive   = true
}


