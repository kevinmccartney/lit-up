# Lit Up API

Python workspace for Lambda functions and utility scripts, managed with **uv**.

## Workspace Structure

This directory uses **uv** for dependency management with native workspace support (like npm workspaces):

- **Shared dev dependencies**: Defined in root `pyproject.toml` (black, pylint, mypy, etc.)
- **Per-Lambda runtime dependencies**: Each Lambda has its own `pyproject.toml` with runtime deps
- **Automatic dependency resolution**: uv automatically installs all Lambda dependencies from workspace members
- **Single virtual environment**: uv manages one `.venv/` with both dev and runtime deps

### Directory Structure

```text
api/
├── pyproject.toml          # Root: dev dependencies + workspace config
├── uv.lock                  # uv lock file (git-committed)
├── .venv/                   # uv-managed virtual environment (git-ignored)
├── config-post/             # Lambda function (workspace member)
│   ├── handler.py
│   └── pyproject.toml      # Runtime deps (boto3, etc.)
├── config-get/              # Lambda function (workspace member)
│   ├── handler.py
│   └── pyproject.toml      # Runtime deps (boto3, etc.)
├── scripts/                 # Utility scripts (legacy, uses own venv)
│   ├── *.py
│   └── requirements.txt
└── [future-lambdas]/        # Additional Lambda functions
    └── pyproject.toml       # Each will be added to workspace members
```

## Prerequisites

Install uv if you haven't already:

```bash
# Recommended: Official installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv

# Verify installation
uv --version
```

## Development Workflow

### Initial Setup

```bash
# Install all dependencies (dev + runtime for all Lambdas)
task api:install
```

This creates a single `.venv/` with:

- All dev tools (black, pylint, mypy, etc.) from root `pyproject.toml`
- All runtime deps from each Lambda's `pyproject.toml` (automatically!)

### Daily Development

```bash
# Use task shortcuts for common operations:
task api:lint              # Lint all Lambdas + scripts
task api:lint:lambda config-post  # Lint specific Lambda
task api:lint:lambda config-get   # Lint specific Lambda
task api:format            # Format all code
task api:isort             # Sort imports
task api:types             # Type check
```

For direct uv commands, see the [uv Commands Reference](#uv-commands-reference) section below.

## Local API server (Flask via Docker Compose)

- Start the full stack (API + UI): `task up`
- API endpoints (pluralized):
  - `http://127.0.0.1:3000/configs` (POST)
  - `http://127.0.0.1:3000/configs/{id}` (GET)
  - `http://127.0.0.1:3000/configs/{id}` (PATCH)
  - `http://127.0.0.1:3000/configs/{id}` (DELETE)
  - `http://127.0.0.1:3000/configs` (GET)
- UI dev server: `http://127.0.0.1:5173`
- Debugging: use the VS Code attach config (`Attach to Local API (Flask)`) to connect to debugpy on port `5890` after running `task up`.

Example requests (from repo root):

```bash
curl -sS -X POST "http://127.0.0.1:3000/configs" \
  -H "content-type: application/json" \
  --data @<(python -c 'import json, pathlib; print(json.loads(pathlib.Path("projects/api/events/config-post.apigw.json").read_text())["body"])')

curl -sS "http://127.0.0.1:3000/configs/<id>"

curl -sS -X PATCH "http://127.0.0.1:3000/configs/<id>" \
  -H "content-type: application/json" \
  -d '{"headerMessage":"patched"}'

curl -sS -X DELETE "http://127.0.0.1:3000/configs/<id>"

curl -sS "http://127.0.0.1:3000/configs"
```

### Working in a Lambda Directory

```bash
# Use tasks from the repo root:
task api:format            # Format all code
task api:lint:lambda config-post  # Lint specific Lambda
task api:lint:lambda config-get   # Lint specific Lambda

# Or use uv directly if needed:
cd projects/api/config-post
uv run black handler.py
uv run pylint handler.py
```

## How It Works

1. **Root `pyproject.toml`**: Defines dev dependencies (black, pylint, etc.) and workspace configuration
2. **Lambda `pyproject.toml`**: Defines runtime dependencies (boto3, etc.)
3. **uv workspace**: Automatically discovers and installs all Lambda dependencies
4. **uv sync**: Installs everything into one `.venv/`
   - Dev tools are available everywhere
   - Runtime deps from all Lambdas are automatically installed
5. **Deployment**: Each Lambda's `pyproject.toml` can be used to export just that Lambda's deps

## Adding a New Lambda

1. Create directory: `mkdir api/my-lambda`
2. Add handler: `api/my-lambda/handler.py`
3. Create `api/my-lambda/pyproject.toml`:

   ```toml
   [project]
   name = "my-lambda"
   version = "0.1.0"
   requires-python = ">=3.13"
   dependencies = [
       "boto3>=1.35.0",
       # ... other runtime deps
   ]
   ```

4. **Add to workspace**: Update root `pyproject.toml`:

   ```toml
   [tool.uv.workspace]
   members = ["config-post", "my-lambda"]
   ```

5. Run `task api:install` to install the new Lambda's deps
6. Dev tools (black, pylint, etc.) are automatically available!

**Note**: uv automatically installs dependencies from all workspace members - no manual syncing needed!

## Building Lambda Deployment Packages

Package and deploy Lambda functions using tasks:

```bash
task api:package:config-post  # Build Lambda zip
task api:deploy:config-post   # Deploy to AWS
task api:package:config-get   # Build Lambda zip
task api:deploy:config-get    # Deploy to AWS
task api:package:config-delete
task api:deploy:config-delete
task api:package:config-list
task api:deploy:config-list
task api:package:config-patch
task api:deploy:config-patch

# Package + deploy all API lambdas
task api:deploy
```

These tasks handle dependency installation in a Lambda-compatible Linux container.

## E2E Testing

E2E tests use **pytest + httpx** and can run against either the local Flask server or deployed API Gateway.

### Running Tests

```bash
# Test against local Flask server (default, requires 'task up' to be running)
task api:e2e

# Explicitly test against local server
task api:e2e:local

# Test against deployed API Gateway (requires API_BASE_URL and API_KEY env vars)
API_BASE_URL=https://api.example.com/dev API_KEY=your-key task api:e2e:deployed
```

### Test Configuration

Tests are configured via environment variables:

- **`API_BASE_URL`**: Base URL for the API (default: `http://127.0.0.1:3000`)
- **`API_KEY`**: API key for deployed API Gateway (not needed for local Flask server)

### Test Structure

```text
tests/
├── __init__.py
├── conftest.py          # Shared fixtures (api_client, sample_config, etc.)
└── test_configs_e2e.py # E2E tests for /configs endpoints
```

### Debugging Tests

Tests can be debugged in VS Code:

1. Set breakpoints in test files
2. Use the Python debugger to run `pytest tests/`
3. Or use the VS Code test runner (if configured)

## uv Commands Reference

```bash
uv sync              # Install/update all dependencies
uv run <command>     # Run a command in the venv
uv python find       # Get Python executable path
uv pip list          # List installed packages
uv add <package>     # Add a dependency (updates pyproject.toml)
uv remove <package>  # Remove a dependency
uv lock              # Update lock file
```

## Legacy Scripts

The `scripts/` directory maintains its own `venv/` for backward compatibility. New Lambda functions should use the uv workspace pattern.
