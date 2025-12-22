# DynamoDB single-table for music domain (configs, playlists, songs)

resource "aws_dynamodb_table" "music" {
  name         = "${var.project}-${var.environment}-music"
  billing_mode = "PAY_PER_REQUEST" # On-demand pricing
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  # Point-in-time recovery for safety (allows restore to any point in last 35 days)
  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "${var.project}-${var.environment}-music"
    Environment = var.environment
    Project     = var.project
  }
}

# IAM policy for Lambda to read/write from DynamoDB music table
resource "aws_iam_role_policy" "lambda_read_write_dynamodb_music" {
  name = "${var.project}-${var.environment}-lambda-read-write-music"
  role = aws_iam_role.lambda_execute_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.music.arn,
          "${aws_dynamodb_table.music.arn}/index/*"
        ]
      }
    ]
  })
}

output "music_table_name" {
  description = "DynamoDB table name for music domain"
  value       = aws_dynamodb_table.music.name
}

output "music_table_arn" {
  description = "DynamoDB table ARN for music domain"
  value       = aws_dynamodb_table.music.arn
}

