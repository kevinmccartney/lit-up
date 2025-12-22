# Config Patch Lambda Handler

Lambda function for the `PATCH /configs/{id}` API Gateway endpoint. Updates an existing playlist config in DynamoDB by `id`. The request body replaces the stored `config` object.

## Deployment

This Lambda is deployed independently from the infrastructure.

After Terraform creates the function, the recommended flow is:

```bash
task api:package:config-patch
task api:deploy:config-patch
```

## Environment Variables

The Lambda expects:

- `CONFIG_TABLE_NAME`: DynamoDB table name (set by Terraform)
- `DYNAMODB_ENDPOINT_URL` (optional): Override DynamoDB endpoint for local dev (e.g. DynamoDB Local)

## Local run/debug (Flask via Docker Compose)

See `projects/api/README.md#local-api-server-flask-via-docker-compose`.
