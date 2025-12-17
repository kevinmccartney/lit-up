# Lit Up Infrastructure

Terraform infrastructure as code for deploying the Lit Up platform on AWS. This infrastructure manages the complete hosting setup including S3, CloudFront, DNS, SSL certificates, and authentication.

## Architecture

The infrastructure deploys:

- **S3 Bucket** - Private bucket for static site hosting (accessed only via CloudFront)
- **CloudFront Distribution** - CDN with Lambda@Edge authentication
- **Route53 DNS** - DNS records for custom domain
- **ACM SSL Certificate** - SSL/TLS certificate for HTTPS
- **SSM Parameters** - Secure storage for authentication credentials
- **Version Config Bucket** - Separate S3 bucket for version-specific configuration

## Features

- 🔒 **Private S3 Bucket** - Static files are not publicly accessible, only through CloudFront
- 🌐 **CloudFront CDN** - Global content delivery with caching
- 🔐 **Lambda@Edge Authentication** - Basic authentication at the edge
- 📦 **Versioned Deployments** - Support for multiple app versions (v1, v2, etc.)
- 🔒 **SSL/TLS** - Automatic SSL certificate management with DNS validation
- 📍 **Custom Domain** - Route53 DNS configuration
- 🔑 **SSM Parameter Store** - Secure credential storage

## Prerequisites

- Terraform >= 1.5
- AWS CLI configured with appropriate credentials
- AWS account with permissions for:
  - S3
  - CloudFront
  - Route53
  - ACM (Certificate Manager)
  - Lambda@Edge
  - SSM Parameter Store
  - IAM

## Environment Variables

The infrastructure requires several environment variables. These should be set in a `.env` file at the repository root:

```bash
# AWS Credentials
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1

# Terraform Backend (for remote state)
export TF_STATE_BUCKET=your-terraform-state-bucket
export TF_STATE_KEY=lit-up/terraform.tfstate
export TF_STATE_REGION=us-east-1
export TF_STATE_DYNAMODB_TABLE=terraform-state-lock
```

## Initial Setup

### 1. Bootstrap Remote State (First Time Only)

If you don't have a Terraform state backend yet, bootstrap it:

```bash
cd bootstrap
terraform init
terraform apply
```

This creates:
- S3 bucket for Terraform state
- DynamoDB table for state locking

### 2. Initialize Infrastructure

From the repository root:

```bash
task infra:init
```

Or manually:

```bash
cd projects/infra
task env:init  # Load .env variables
terraform init -reconfigure \
  -backend-config="bucket=$TF_STATE_BUCKET" \
  -backend-config="key=$TF_STATE_KEY" \
  -backend-config="region=$TF_STATE_REGION" \
  -backend-config="dynamodb_table=$TF_STATE_DYNAMODB_TABLE" \
  -backend-config="encrypt=true"
```

### 3. Plan Changes

Preview infrastructure changes:

```bash
task infra:plan
```

Or manually:

```bash
cd projects/infra
terraform plan
```

### 4. Apply Infrastructure

Deploy the infrastructure:

```bash
task infra:apply
```

Or manually:

```bash
cd projects/infra
terraform apply
```

**Note**: SSL certificate validation may take several minutes. Terraform will wait for DNS validation to complete.

## Configuration

### Variables

Key variables can be customized in `variables.tf` or via command line:

- `project` - Project identifier (default: "lit-up")
- `environment` - Environment name (default: "dev")
- `aws_region` - AWS region (default: "us-east-1")
- `auth_username` - Basic auth username (default: "admin")
- `auth_password` - Basic auth password (default: "changeme123")
- `ACTIVE_VERSIONS` - Comma-separated list of active versions (default: "v1,v2")

### Custom Domain

The infrastructure is configured for `lit-up.kevinmccartney.is`. To use a different domain:

1. Update `dns.tf` with your Route53 zone
2. Update `ssl-certificate.tf` with your domain name
3. Update `cloudfront.tf` with your domain in the aliases

## Infrastructure Components

### S3 Static Site Bucket

- **Name**: `{project}-{environment}-static-site`
- **Access**: Private (only accessible via CloudFront)
- **Purpose**: Hosts the built React application files

### CloudFront Distribution

- **Origin**: S3 bucket via Origin Access Control
- **Authentication**: Lambda@Edge viewer request function
- **Caching**: Configured for static assets
- **Custom Domain**: Supports custom domain with SSL

### Lambda@Edge Authentication

Basic authentication is handled at the CloudFront edge using a Lambda@Edge function. Credentials are stored in SSM Parameter Store and read by the Lambda function.

### SSL Certificate

- **Provider**: AWS Certificate Manager (ACM)
- **Validation**: DNS validation via Route53
- **Region**: Must be in `us-east-1` for CloudFront

### Version Configuration

A separate S3 bucket (`{project}-{environment}-version-config`) is provided for version-specific configuration files that can be managed independently of deployments.

## Outputs

After applying, Terraform outputs:

- `s3_bucket_name` - S3 bucket name for deployments
- `cloudfront_distribution_id` - CloudFront distribution ID
- `cloudfront_url` - CloudFront distribution URL
- `website_url` - Custom domain URL (if configured)
- `certificate_arn` - SSL certificate ARN
- `certificate_validation_status` - Certificate validation status

View outputs:

```bash
cd projects/infra
terraform output
```

## Common Tasks

### Check SSL Certificate Status

```bash
task infra:ssl_status
```

### View SSL Certificate Info

```bash
task infra:ssl_info
```

### Destroy Infrastructure

⚠️ **Warning**: This will delete all infrastructure resources.

```bash
task infra:destroy
```

## Deployment Integration

The infrastructure is integrated with the deployment process. When you run `task ui:deploy`, it:

1. Gets the S3 bucket name from Terraform outputs
2. Syncs files to `s3://{bucket}/{version}/`
3. Invalidates CloudFront cache
4. Displays the website URL

## Security Considerations

- S3 buckets are private and only accessible via CloudFront
- Authentication credentials are stored in SSM Parameter Store (encrypted)
- Lambda@Edge function reads credentials from SSM at runtime
- SSL/TLS encryption for all traffic
- Origin Access Control prevents direct S3 access

## Troubleshooting

### SSL Certificate Not Validating

1. Check Route53 DNS records were created
2. Verify DNS propagation: `dig lit-up.kevinmccartney.is`
3. Wait up to 30 minutes for validation
4. Check certificate status: `task infra:ssl_status`

### CloudFront Not Updating

After deploying, invalidate the CloudFront cache:

```bash
DISTRIBUTION_ID=$(cd projects/infra && terraform output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"
```

### Authentication Not Working

1. Verify SSM parameters exist:
   ```bash
   aws ssm get-parameter --name "/lit-up/dev/auth/username"
   aws ssm get-parameter --name "/lit-up/dev/auth/password" --with-decryption
   ```
2. Check Lambda@Edge function has permissions to read SSM
3. Verify Lambda function is deployed to all edge locations

## File Structure

```
infra/
├── backend.tf              # Terraform backend configuration
├── provider.aws.tf         # AWS provider configuration
├── variables.tf            # Input variables
├── versions.tf            # Provider version constraints
├── s3-static-site.tf       # S3 bucket for static site
├── s3-version-config.tf   # S3 bucket for version configs
├── cloudfront.tf          # CloudFront distribution
├── ssl-certificate.tf     # ACM SSL certificate
├── dns.tf                 # Route53 DNS records
├── route53-record.tf      # Additional Route53 config
├── ssm.tf                 # SSM Parameter Store
├── cf-viewer-request/     # Lambda@Edge function
│   └── index.js
└── bootstrap/             # Bootstrap Terraform state
    ├── main.tf
    └── ...
```

## Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [Lambda@Edge Documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-edge.html)

