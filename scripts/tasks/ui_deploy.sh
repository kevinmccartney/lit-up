#!/usr/bin/env bash
set -euo pipefail

# Deploy UI to S3 and invalidate CloudFront cache
# Usage: ui_deploy.sh [VERSION]

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR/projects/ui"

# Use VERSION env var or default to v1 (set early so build process can use it)
export VERSION="${VERSION:-${1:-v1}}"
echo "📌 Building version: $VERSION"

echo "Cleaning dist directory..."
rm -rf dist/*

# Process songs, generate config, concatenate playlist, generate favicon, and build
cd "$ROOT_DIR"
task api:process_songs
task api:generate_config
task api:concatenate_playlist
task api:generate_favicon
task ui:build

# Copy .out to dist (hack until we have a proper API)
cd "$ROOT_DIR/projects/ui"
echo "Copying .out to dist..."
cp -r .out/* dist/ || {
  echo "❌ Error: Could not copy .out to dist"
  exit 1
}
echo "✅ .out copied to dist!"

# Deploy to S3
echo "🚀 Deploying React app to S3..."
BUCKET_NAME=$(cd "$ROOT_DIR/projects/infra" && terraform output -raw s3_bucket_name)
if [ -z "$BUCKET_NAME" ]; then
  echo "❌ Error: Could not get S3 bucket name from Terraform outputs"
  echo "Make sure you've run 'task infra:apply' first"
  exit 1
fi

echo "📦 Deploying to bucket: $BUCKET_NAME"
aws s3 sync dist/ "s3://$BUCKET_NAME/$VERSION" --delete || {
  echo "❌ Deployment failed"
  exit 1
}
echo "✅ S3 sync successful!"

# Invalidate CloudFront cache
DISTRIBUTION_ID=$(cd "$ROOT_DIR/projects/infra" && terraform output -raw cloudfront_distribution_id)
if [ -n "$DISTRIBUTION_ID" ]; then
  echo "🔄 Invalidating CloudFront cache..."
  aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" --paths "/*" || {
    echo "⚠️  CloudFront invalidation failed, but deployment was successful"
  }
else
  echo "⚠️  Could not get CloudFront distribution ID, skipping invalidation"
fi

echo "✅ Deployment successful!"
echo "🌐 Your app is available at: $(cd "$ROOT_DIR/projects/infra" && terraform output -raw website_url)"

