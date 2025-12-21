#!/usr/bin/env bash
set -euo pipefail

# Deploy a Lambda function to AWS
# Usage: lambda_deploy.sh LAMBDA_NAME [PROJECT] [ENVIRONMENT] [AWS_REGION]

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR/projects/api"

if ! command -v aws >/dev/null 2>&1; then
  echo "❌ AWS CLI is not installed"
  echo "  Install with: https://aws.amazon.com/cli/"
  exit 1
fi

LAMBDA_NAME="${1:-}"
if [ -z "$LAMBDA_NAME" ]; then
  echo "❌ Error: Lambda name is required"
  echo "Usage: lambda_deploy.sh LAMBDA_NAME [PROJECT] [ENVIRONMENT] [AWS_REGION]"
  exit 1
fi

ZIP_FILE=".lambda-package/$LAMBDA_NAME.zip"

if [ ! -f "$ZIP_FILE" ]; then
  echo "❌ Zip file not found: $ZIP_FILE"
  echo "  Run 'task api:package:$LAMBDA_NAME' first to create the package"
  exit 1
fi

# Get function name from environment variables or use defaults
PROJECT="${PROJECT:-${2:-lit-up}}"
ENVIRONMENT="${ENVIRONMENT:-${3:-dev}}"
AWS_REGION="${AWS_REGION:-${4:-us-east-1}}"
FUNCTION_NAME="${PROJECT}-${ENVIRONMENT}-${LAMBDA_NAME}"

echo "🚀 Deploying $LAMBDA_NAME Lambda to AWS..."
echo "   Function: $FUNCTION_NAME"
echo "   Region: $AWS_REGION"
echo "   Zip: $ZIP_FILE ($(du -h "$ZIP_FILE" | cut -f1))"

# Update Lambda function code
aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --zip-file "fileb://$ZIP_FILE" \
  --region "$AWS_REGION" \
  --output json > /dev/null || {
  echo "❌ Failed to deploy Lambda"
  exit 1
}

echo "✅ Lambda deployed successfully!"
echo "   Waiting for update to complete..."

# Wait for the update to complete
aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME" \
  --region "$AWS_REGION" || {
  echo "⚠️  Deployment initiated, but status check timed out"
  echo "   Check status with: aws lambda get-function --function-name $FUNCTION_NAME --region $AWS_REGION"
  exit 1
}

echo "✅ Lambda update completed and ready"

