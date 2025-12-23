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
  echo "  Docker is required to package native dependencies"
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

# Copy shared models into the package (ensures models/ is present even if installer skips)
if [ -d "models" ]; then
  echo "  Copying shared models..."
  cp -a models "$PACKAGE_DIR/"
fi

# Use Docker to install dependencies in Lambda-compatible Linux environment with uv
echo "  Installing runtime dependencies and bundling models..."
docker run --rm \
  --platform "$DOCKER_PLATFORM" \
  --entrypoint /bin/bash \
  -v "$(pwd):/workspace" \
  -v "$(pwd)/$PACKAGE_DIR:/var/task" \
  public.ecr.aws/lambda/python:3.13 \
  -c "
set -euo pipefail
cd /workspace

# Ensure tar is available (required by uv installer)
if ! command -v tar >/dev/null 2>&1; then
  if command -v dnf >/dev/null 2>&1; then
    dnf install -y tar gzip >/dev/null 2>&1
  elif command -v yum >/dev/null 2>&1; then
    yum install -y tar gzip >/dev/null 2>&1
  else
    echo 'tar is required but no package manager (dnf/yum) was found' >&2
    exit 1
  fi
fi

# Install uv (installer puts binaries in $HOME/.local/bin)
curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1
export PATH="\$HOME/.local/bin:\$HOME/.cargo/bin:\$PATH"

# Copy models source files directly (no need to install as package)
if [ -d models ] && [ -f models/pyproject.toml ]; then
  echo '  Copying models source files...'
  mkdir -p /var/task/models
  cp models/*.py /var/task/models/
  echo '  Models copied ✓'
fi

# Install Lambda package and its dependencies (excluding models, which we copied above)
uv pip install --target /var/task --no-cache-dir --system ./$LAMBDA_DIR >/dev/null 2>&1
"

# Create zip file
echo "  Creating zip archive..."
# Use Python to create zip with files at root (not nested in a folder)
python3 <<PYTHON_EOF
import os
import zipfile
from pathlib import Path

package_dir = Path("$PACKAGE_DIR")
zip_path = Path("$ZIP_FILE")

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(package_dir):
        for file in files:
            file_path = Path(root) / file
            # Use relative path from package_dir so files are at root of zip
            arcname = file_path.relative_to(package_dir)
            zipf.write(file_path, arcname)
PYTHON_EOF

# Clean up package directory (keep zip)
rm -rf "$PACKAGE_DIR"

echo "✅ Lambda packaged: $ZIP_FILE ($(du -h "$ZIP_FILE" | cut -f1))"

