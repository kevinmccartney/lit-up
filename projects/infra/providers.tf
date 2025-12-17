provider "aws" {
  # Credentials and region are read from the environment by default.
  # Supported env vars:
  # - AWS_ACCESS_KEY_ID
  # - AWS_SECRET_ACCESS_KEY
  # - AWS_SESSION_TOKEN (optional, for temporary creds)
  # - AWS_REGION or AWS_DEFAULT_REGION
}

provider "archive" {}
