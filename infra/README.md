# Infra - Terraform (AWS)

Minimal Terraform setup using the AWS provider. Credentials and region are sourced from environment variables.

## Prerequisites

- Terraform >= 1.5
- AWS credentials via environment variables

## Environment variables

Export the following environment variables (or use your preferred credential helper):

```bash
export AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXXX
export AWS_SECRET_ACCESS_KEY=YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
# Optional if using temporary credentials
export AWS_SESSION_TOKEN=ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ
# Region (required if not in your shared config/profile)
export AWS_REGION=us-east-1
# or
export AWS_DEFAULT_REGION=us-east-1
```

## Usage

### 1) Create IAM service account (recommended)

Instead of using root AWS credentials, create a dedicated service account:

```bash
# Use root credentials temporarily to create the service account
export AWS_ACCESS_KEY_ID=your_root_access_key
export AWS_SECRET_ACCESS_KEY=your_root_secret_key
export AWS_REGION=us-east-1

# Create IAM user with minimal required permissions
cd infra/iam
terraform init
terraform apply

# Save the generated credentials (terraform_access_key_id, terraform_secret_access_key)
# These won't be shown again!
```

Then update your `.env` file with the service account credentials instead of root.

### 2) Bootstrap remote state (optional)

Creates S3 bucket + DynamoDB table for remote state/locking. Uses your AWS env.

```bash
cd infra/bootstrap
terraform init
terraform apply
```

### 3) Configure environment variables via .env

Copy `.env.sample` to `.env` and fill in values:

```bash
cd ..
cp .env.sample .env
# edit .env with your values
```

Load the env vars into your shell for the next commands:

```bash
set -a; source .env; set +a
```

### 4) Initialize backend (no flags required)

The S3 backend reads credentials from `AWS_*` env vars. The `.env` also sets
`TF_CLI_ARGS_init` so Terraform will automatically apply the backend settings
on `init`.

```bash
terraform init -reconfigure
```

### 5) Plan/apply as usual

```bash
terraform plan
```

Note: The root provider already uses `AWS_*` env vars.
