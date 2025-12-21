#!/usr/bin/env bash
set -euo pipefail

# Package a Lambda function into a deployment zip using Docker
# Usage: lambda_package.sh LAMBDA_NAME [DOCKER_PLATFORM]

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR/projects/api"

LAMBDA_NAME="${1:-}"
if [ -z "$LAMBDA_NAME" ]; then
  echo "❌ Error: Lambda name is required"
  echo "Usage: lambda_package.sh LAMBDA_NAME [DOCKER_PLATFORM]"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "❌ Docker is not installed or not running"
  echo "  Docker is required to package native dependencies (like Pydantic) for Lambda"
  exit 1
fi

LAMBDA_DIR="$LAMBDA_NAME"
PACKAGE_DIR=".lambda-package/$LAMBDA_NAME"
ZIP_FILE=".lambda-package/$LAMBDA_NAME.zip"
# Lambda defaults to x86_64 unless you explicitly set architectures = ["arm64"] in Terraform
# Apple Silicon Macs will often pull ARM images unless we force linux/amd64.
DOCKER_PLATFORM="${DOCKER_PLATFORM:-${2:-linux/amd64}}"

if [ ! -d "$LAMBDA_DIR" ] || [ ! -f "$LAMBDA_DIR/pyproject.toml" ]; then
  echo "❌ Error: Lambda '$LAMBDA_NAME' not found or missing pyproject.toml"
  exit 1
fi

echo "📦 Packaging $LAMBDA_NAME Lambda..."

# Clean up any existing package directory
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"
# Ensure we don't accidentally keep stale entries in an existing zip (zip updates by default)
rm -f "$ZIP_FILE"

# Copy handler file
echo "  Copying handler..."
cp "$LAMBDA_DIR/handler.py" "$PACKAGE_DIR/"

# Use Docker to install dependencies in Lambda-compatible Linux environment
echo "  Installing runtime dependencies..."
# Extract dependencies from pyproject.toml
DEPS=$(python3 -c "import tomllib; f = open('$LAMBDA_DIR/pyproject.toml', 'rb'); data = tomllib.load(f); f.close(); deps = data.get('project', {}).get('dependencies', []); print(' '.join(deps))" 2>/dev/null || echo "")

if [ -z "$DEPS" ]; then
  echo "  ⚠️  No runtime dependencies found (or error reading pyproject.toml)"
else
  # Use Docker with Python 3.13 Lambda base image to install dependencies
  # This ensures we get Linux-compatible wheels for native extensions like pydantic-core
  # Override entrypoint to use bash instead of Lambda handler
  docker run --rm \
    --platform "$DOCKER_PLATFORM" \
    --entrypoint /bin/bash \
    -v "$(pwd)/$PACKAGE_DIR:/var/task" \
    -v "$(pwd)/$LAMBDA_DIR:/lambda-source" \
    public.ecr.aws/lambda/python:3.13 \
    -c "set -euo pipefail; pip install --upgrade pip >/dev/null; pip install --target /var/task --no-cache-dir $DEPS >/dev/null; PYTHONPATH=/var/task python3 -c 'import pydantic_core._pydantic_core' >/dev/null"
fi

# Verify pydantic-core binary extension exists (this is what Lambda needs)
PCORE_SO_COUNT=$(find "$PACKAGE_DIR" -maxdepth 2 -type f -name "_pydantic_core*.so" 2>/dev/null | wc -l | tr -d ' ')
if [ "$PCORE_SO_COUNT" -gt 0 ]; then
  : # ok
else
  echo "  ❌ pydantic_core native extension NOT found in package directory"
  echo "     This will crash on Lambda with: No module named 'pydantic_core._pydantic_core'"
  exit 1
fi

# Create zip file
echo "  Creating zip archive..."
cd "$PACKAGE_DIR"
zip -r "../$LAMBDA_NAME.zip" . -q
cd ../..

# Verify zip contents (ensure we produced the right arch)
if unzip -l "$ZIP_FILE" | grep -Eq "pydantic_core/_pydantic_core.*x86_64-linux-gnu\.so"; then
  : # ok
else
  echo "  ❌ Expected x86_64 Linux pydantic_core native extension NOT found in zip"
  echo "     (If you're deploying an ARM64 Lambda, set DOCKER_PLATFORM=linux/arm64 and update the check.)"
  exit 1
fi

# Clean up package directory (keep zip)
rm -rf "$PACKAGE_DIR"

echo "✅ Lambda packaged: $ZIP_FILE ($(du -h "$ZIP_FILE" | cut -f1))"

