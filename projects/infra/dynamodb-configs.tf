# DynamoDB table for playlist configs (versioned)

resource "aws_dynamodb_table" "configs" {
  name         = "${var.project}-${var.environment}-configs"
  billing_mode = "PAY_PER_REQUEST" # On-demand pricing
  hash_key     = "version"

  attribute {
    name = "version"
    type = "S"
  }

  # Point-in-time recovery for safety (allows restore to any point in last 35 days)
  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "${var.project}-${var.environment}-configs"
    Environment = var.environment
    Project     = var.project
  }
}

# IAM policy for Lambda to read/write from DynamoDB configs table
resource "aws_iam_role_policy" "lambda_read_write_dynamodb_configs" {
  name = "${var.project}-${var.environment}-lambda-read-write-configs"
  role = aws_iam_role.lambda_execute_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:PutItem"
        ]
        Resource = "${aws_dynamodb_table.configs.arn}"
      }
    ]
  })
}

output "configs_table_name" {
  description = "DynamoDB table name for configs"
  value       = aws_dynamodb_table.configs.name
}

output "configs_table_arn" {
  description = "DynamoDB table ARN for configs"
  value       = aws_dynamodb_table.configs.arn
}

