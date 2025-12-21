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
task api:format            # Format all code
task api:isort             # Sort imports
task api:types             # Type check
```

For direct uv commands, see the [uv Commands Reference](#uv-commands-reference) section below.

### Working in a Lambda Directory

```bash
# Use tasks from the repo root:
task api:format            # Format all code
task api:lint:lambda config-post  # Lint specific Lambda

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
```

These tasks handle dependency installation in a Lambda-compatible Linux container.

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
