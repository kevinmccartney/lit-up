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
  architectures    = ["arm64"]
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
  architectures    = ["arm64"]
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      MUSIC_TABLE_NAME = aws_dynamodb_table.music.name
    }
  }

  tags = {
    Name        = "${var.project}-${var.environment}-config-post"
    Environment = var.environment
  }
}

# Lambda function for GET /config/{id} (Python, deployed from api project)
data "archive_file" "config_get_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-config-get-placeholder.zip"
  source {
    content  = "# Placeholder - Lambda code deployed separately from api project"
    filename = "placeholder.txt"
  }
}

resource "aws_lambda_function" "config_get_function" {
  filename         = data.archive_file.config_get_lambda_zip.output_path
  function_name    = "${var.project}-${var.environment}-config-get"
  role             = aws_iam_role.lambda_execute_role.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.config_get_lambda_zip.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      MUSIC_TABLE_NAME = aws_dynamodb_table.music.name
    }
  }

  tags = {
    Name        = "${var.project}-${var.environment}-config-get"
    Environment = var.environment
  }
}

# Lambda function for DELETE /config/{id} (Python, deployed from api project)
data "archive_file" "config_delete_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-config-delete-placeholder.zip"
  source {
    content  = "# Placeholder - Lambda code deployed separately from api project"
    filename = "placeholder.txt"
  }
}

resource "aws_lambda_function" "config_delete_function" {
  filename         = data.archive_file.config_delete_lambda_zip.output_path
  function_name    = "${var.project}-${var.environment}-config-delete"
  role             = aws_iam_role.lambda_execute_role.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.config_delete_lambda_zip.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      MUSIC_TABLE_NAME = aws_dynamodb_table.music.name
    }
  }

  tags = {
    Name        = "${var.project}-${var.environment}-config-delete"
    Environment = var.environment
  }
}

# Lambda function for GET /configs (Python, deployed from api project)
data "archive_file" "config_list_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-config-list-placeholder.zip"
  source {
    content  = "# Placeholder - Lambda code deployed separately from api project"
    filename = "placeholder.txt"
  }
}

resource "aws_lambda_function" "config_list_function" {
  filename         = data.archive_file.config_list_lambda_zip.output_path
  function_name    = "${var.project}-${var.environment}-config-list"
  role             = aws_iam_role.lambda_execute_role.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.config_list_lambda_zip.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      MUSIC_TABLE_NAME = aws_dynamodb_table.music.name
    }
  }

  tags = {
    Name        = "${var.project}-${var.environment}-config-list"
    Environment = var.environment
  }
}

# Lambda function for PATCH /configs/{id} (Python, deployed from api project)
data "archive_file" "config_patch_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-config-patch-placeholder.zip"
  source {
    content  = "# Placeholder - Lambda code deployed separately from api project"
    filename = "placeholder.txt"
  }
}

data "archive_file" "song_post_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-song-post-placeholder.zip"
  source {
    content  = "# Placeholder - Lambda code deployed separately from api project"
    filename = "placeholder.txt"
  }
}

data "archive_file" "song_get_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-song-get-placeholder.zip"
  source {
    content  = "# Placeholder - Lambda code deployed separately from api project"
    filename = "placeholder.txt"
  }
}

data "archive_file" "song_delete_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-song-delete-placeholder.zip"
  source {
    content  = "# Placeholder - Lambda code deployed separately from api project"
    filename = "placeholder.txt"
  }
}

data "archive_file" "song_patch_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-song-patch-placeholder.zip"
  source {
    content  = "# Placeholder - Lambda code deployed separately from api project"
    filename = "placeholder.txt"
  }
}

data "archive_file" "song_list_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/lambda-song-list-placeholder.zip"
  source {
    content  = "# Placeholder - Lambda code deployed separately from api project"
    filename = "placeholder.txt"
  }
}

resource "aws_lambda_function" "config_patch_function" {
  filename         = data.archive_file.config_patch_lambda_zip.output_path
  function_name    = "${var.project}-${var.environment}-config-patch"
  role             = aws_iam_role.lambda_execute_role.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.config_patch_lambda_zip.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      MUSIC_TABLE_NAME = aws_dynamodb_table.music.name
    }
  }

  tags = {
    Name        = "${var.project}-${var.environment}-config-patch"
    Environment = var.environment
  }
}

resource "aws_lambda_function" "song_post_function" {
  filename         = data.archive_file.song_post_lambda_zip.output_path
  function_name    = "${var.project}-${var.environment}-song-post"
  role             = aws_iam_role.lambda_execute_role.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.song_post_lambda_zip.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      MUSIC_TABLE_NAME = aws_dynamodb_table.music.name
    }
  }

  tags = {
    Name        = "${var.project}-${var.environment}-song-post"
    Environment = var.environment
  }
}

resource "aws_lambda_function" "song_get_function" {
  filename         = data.archive_file.song_get_lambda_zip.output_path
  function_name    = "${var.project}-${var.environment}-song-get"
  role             = aws_iam_role.lambda_execute_role.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.song_get_lambda_zip.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      MUSIC_TABLE_NAME = aws_dynamodb_table.music.name
    }
  }

  tags = {
    Name        = "${var.project}-${var.environment}-song-get"
    Environment = var.environment
  }
}

resource "aws_lambda_function" "song_delete_function" {
  filename         = data.archive_file.song_delete_lambda_zip.output_path
  function_name    = "${var.project}-${var.environment}-song-delete"
  role             = aws_iam_role.lambda_execute_role.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.song_delete_lambda_zip.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      MUSIC_TABLE_NAME = aws_dynamodb_table.music.name
    }
  }

  tags = {
    Name        = "${var.project}-${var.environment}-song-delete"
    Environment = var.environment
  }
}

resource "aws_lambda_function" "song_patch_function" {
  filename         = data.archive_file.song_patch_lambda_zip.output_path
  function_name    = "${var.project}-${var.environment}-song-patch"
  role             = aws_iam_role.lambda_execute_role.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.song_patch_lambda_zip.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      MUSIC_TABLE_NAME = aws_dynamodb_table.music.name
    }
  }

  tags = {
    Name        = "${var.project}-${var.environment}-song-patch"
    Environment = var.environment
  }
}

resource "aws_lambda_function" "song_list_function" {
  filename         = data.archive_file.song_list_lambda_zip.output_path
  function_name    = "${var.project}-${var.environment}-song-list"
  role             = aws_iam_role.lambda_execute_role.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.song_list_lambda_zip.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  memory_size      = 128

  environment {
    variables = {
      MUSIC_TABLE_NAME = aws_dynamodb_table.music.name
    }
  }

  tags = {
    Name        = "${var.project}-${var.environment}-song-list"
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
  path_part   = "configs"
}

resource "aws_api_gateway_resource" "config_id" {
  rest_api_id = aws_api_gateway_rest_api.lit_up_api.id
  parent_id   = aws_api_gateway_resource.config.id
  path_part   = "{id}"
}

resource "aws_api_gateway_resource" "songs" {
  rest_api_id = aws_api_gateway_rest_api.lit_up_api.id
  parent_id   = aws_api_gateway_rest_api.lit_up_api.root_resource_id
  path_part   = "songs"
}

resource "aws_api_gateway_resource" "song_id" {
  rest_api_id = aws_api_gateway_rest_api.lit_up_api.id
  parent_id   = aws_api_gateway_resource.songs.id
  path_part   = "{id}"
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

resource "aws_api_gateway_method" "config_get" {
  rest_api_id      = aws_api_gateway_rest_api.lit_up_api.id
  resource_id      = aws_api_gateway_resource.config_id.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method" "config_delete" {
  rest_api_id      = aws_api_gateway_rest_api.lit_up_api.id
  resource_id      = aws_api_gateway_resource.config_id.id
  http_method      = "DELETE"
  authorization    = "NONE"
  api_key_required = true
  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method" "config_list" {
  rest_api_id      = aws_api_gateway_rest_api.lit_up_api.id
  resource_id      = aws_api_gateway_resource.config.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_method" "config_patch" {
  rest_api_id      = aws_api_gateway_rest_api.lit_up_api.id
  resource_id      = aws_api_gateway_resource.config_id.id
  http_method      = "PATCH"
  authorization    = "NONE"
  api_key_required = true
  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method" "song_post" {
  rest_api_id      = aws_api_gateway_rest_api.lit_up_api.id
  resource_id      = aws_api_gateway_resource.songs.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_method" "song_list" {
  rest_api_id      = aws_api_gateway_rest_api.lit_up_api.id
  resource_id      = aws_api_gateway_resource.songs.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_method" "song_get" {
  rest_api_id      = aws_api_gateway_rest_api.lit_up_api.id
  resource_id      = aws_api_gateway_resource.song_id.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method" "song_delete" {
  rest_api_id      = aws_api_gateway_rest_api.lit_up_api.id
  resource_id      = aws_api_gateway_resource.song_id.id
  http_method      = "DELETE"
  authorization    = "NONE"
  api_key_required = true
  request_parameters = {
    "method.request.path.id" = true
  }
}

resource "aws_api_gateway_method" "song_patch" {
  rest_api_id      = aws_api_gateway_rest_api.lit_up_api.id
  resource_id      = aws_api_gateway_resource.song_id.id
  http_method      = "PATCH"
  authorization    = "NONE"
  api_key_required = true
  request_parameters = {
    "method.request.path.id" = true
  }
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

resource "aws_api_gateway_integration" "config_get" {
  rest_api_id             = aws_api_gateway_rest_api.lit_up_api.id
  resource_id             = aws_api_gateway_resource.config_id.id
  http_method             = aws_api_gateway_method.config_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.config_get_function.invoke_arn
}

resource "aws_api_gateway_integration" "config_delete" {
  rest_api_id             = aws_api_gateway_rest_api.lit_up_api.id
  resource_id             = aws_api_gateway_resource.config_id.id
  http_method             = aws_api_gateway_method.config_delete.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.config_delete_function.invoke_arn
}

resource "aws_api_gateway_integration" "config_list" {
  rest_api_id             = aws_api_gateway_rest_api.lit_up_api.id
  resource_id             = aws_api_gateway_resource.config.id
  http_method             = aws_api_gateway_method.config_list.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.config_list_function.invoke_arn
}

resource "aws_api_gateway_integration" "config_patch" {
  rest_api_id             = aws_api_gateway_rest_api.lit_up_api.id
  resource_id             = aws_api_gateway_resource.config_id.id
  http_method             = aws_api_gateway_method.config_patch.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.config_patch_function.invoke_arn
}

resource "aws_api_gateway_integration" "song_post" {
  rest_api_id             = aws_api_gateway_rest_api.lit_up_api.id
  resource_id             = aws_api_gateway_resource.songs.id
  http_method             = aws_api_gateway_method.song_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.song_post_function.invoke_arn
}

resource "aws_api_gateway_integration" "song_list" {
  rest_api_id             = aws_api_gateway_rest_api.lit_up_api.id
  resource_id             = aws_api_gateway_resource.songs.id
  http_method             = aws_api_gateway_method.song_list.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.song_list_function.invoke_arn
}

resource "aws_api_gateway_integration" "song_get" {
  rest_api_id             = aws_api_gateway_rest_api.lit_up_api.id
  resource_id             = aws_api_gateway_resource.song_id.id
  http_method             = aws_api_gateway_method.song_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.song_get_function.invoke_arn
}

resource "aws_api_gateway_integration" "song_delete" {
  rest_api_id             = aws_api_gateway_rest_api.lit_up_api.id
  resource_id             = aws_api_gateway_resource.song_id.id
  http_method             = aws_api_gateway_method.song_delete.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.song_delete_function.invoke_arn
}

resource "aws_api_gateway_integration" "song_patch" {
  rest_api_id             = aws_api_gateway_rest_api.lit_up_api.id
  resource_id             = aws_api_gateway_resource.song_id.id
  http_method             = aws_api_gateway_method.song_patch.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.song_patch_function.invoke_arn
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
  source_arn    = "${aws_api_gateway_rest_api.lit_up_api.execution_arn}/*/POST/configs"
}

resource "aws_lambda_permission" "allow_apigw_invoke_config_get" {
  statement_id  = "AllowExecutionFromApiGatewayConfigGet"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.config_get_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.lit_up_api.execution_arn}/*/GET/configs/*"
}

resource "aws_lambda_permission" "allow_apigw_invoke_config_delete" {
  statement_id  = "AllowExecutionFromApiGatewayConfigDelete"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.config_delete_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.lit_up_api.execution_arn}/*/DELETE/configs/*"
}

resource "aws_lambda_permission" "allow_apigw_invoke_config_list" {
  statement_id  = "AllowExecutionFromApiGatewayConfigList"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.config_list_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.lit_up_api.execution_arn}/*/GET/configs"
}

resource "aws_lambda_permission" "allow_apigw_invoke_config_patch" {
  statement_id  = "AllowExecutionFromApiGatewayConfigPatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.config_patch_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.lit_up_api.execution_arn}/*/PATCH/configs/*"
}

resource "aws_lambda_permission" "allow_apigw_invoke_song_post" {
  statement_id  = "AllowExecutionFromApiGatewaySongPost"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.song_post_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.lit_up_api.execution_arn}/*/POST/songs"
}

resource "aws_lambda_permission" "allow_apigw_invoke_song_get" {
  statement_id  = "AllowExecutionFromApiGatewaySongGet"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.song_get_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.lit_up_api.execution_arn}/*/GET/songs/*"
}

resource "aws_lambda_permission" "allow_apigw_invoke_song_delete" {
  statement_id  = "AllowExecutionFromApiGatewaySongDelete"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.song_delete_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.lit_up_api.execution_arn}/*/DELETE/songs/*"
}

resource "aws_lambda_permission" "allow_apigw_invoke_song_patch" {
  statement_id  = "AllowExecutionFromApiGatewaySongPatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.song_patch_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.lit_up_api.execution_arn}/*/PATCH/songs/*"
}

resource "aws_lambda_permission" "allow_apigw_invoke_song_list" {
  statement_id  = "AllowExecutionFromApiGatewaySongList"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.song_list_function.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.lit_up_api.execution_arn}/*/GET/songs"
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
      aws_api_gateway_resource.config_id.id,
      aws_api_gateway_method.config_post.id,
      aws_api_gateway_method.config_post.api_key_required,
      aws_api_gateway_integration.config_post.id,
      aws_api_gateway_method.config_get.id,
      aws_api_gateway_method.config_get.api_key_required,
      aws_api_gateway_integration.config_get.id,
      aws_api_gateway_method.config_delete.id,
      aws_api_gateway_method.config_delete.api_key_required,
      aws_api_gateway_integration.config_delete.id,
      aws_api_gateway_resource.config.id,
      aws_api_gateway_method.config_list.id,
      aws_api_gateway_method.config_list.api_key_required,
      aws_api_gateway_integration.config_list.id,
      aws_api_gateway_method.config_patch.id,
      aws_api_gateway_method.config_patch.api_key_required,
      aws_api_gateway_integration.config_patch.id,
      aws_api_gateway_resource.songs.id,
      aws_api_gateway_method.song_post.id,
      aws_api_gateway_method.song_post.api_key_required,
      aws_api_gateway_integration.song_post.id,
      aws_api_gateway_method.song_list.id,
      aws_api_gateway_method.song_list.api_key_required,
      aws_api_gateway_integration.song_list.id,
      aws_api_gateway_resource.song_id.id,
      aws_api_gateway_method.song_get.id,
      aws_api_gateway_method.song_get.api_key_required,
      aws_api_gateway_integration.song_get.id,
      aws_api_gateway_method.song_delete.id,
      aws_api_gateway_method.song_delete.api_key_required,
      aws_api_gateway_integration.song_delete.id,
      aws_api_gateway_method.song_patch.id,
      aws_api_gateway_method.song_patch.api_key_required,
      aws_api_gateway_integration.song_patch.id,
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


