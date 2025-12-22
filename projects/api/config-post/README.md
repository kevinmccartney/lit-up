# Config Post Lambda Handler

Lambda function for the `POST /configs` API Gateway endpoint. Reads playlist configs from DynamoDB.

## Deployment

This Lambda is deployed independently from the infrastructure.

After Terraform creates the function, the recommended flow is:

- Build a Lambda-compatible zip using the repo task (installs deps from `pyproject.toml` in a Lambda Linux container):

```bash
task api:package:config-post
task api:deploy:config-post
```

Or use the AWS Console to upload the zip file.

## Environment Variables

The Lambda expects:

- `MUSIC_TABLE_NAME`: DynamoDB single-table name (set by Terraform)
- `DYNAMODB_ENDPOINT_URL` (optional): Override DynamoDB endpoint for local dev (e.g. DynamoDB Local)

## Local run/debug (Flask via Docker Compose)

See `projects/api/README.md#local-api-server-flask-via-docker-compose`.
