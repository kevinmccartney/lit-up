# Config List Lambda Handler

Lambda function for the `GET /configs` API Gateway endpoint. Lists all saved playlist configs from DynamoDB.

## Deployment

This Lambda is deployed independently from the infrastructure.

After Terraform creates the function, the recommended flow is:

```bash
task api:package:config-list
task api:deploy:config-list
```

## Environment Variables

The Lambda expects:

- `MUSIC_TABLE_NAME`: DynamoDB single-table name (set by Terraform)
- `DYNAMODB_ENDPOINT_URL` (optional): Override DynamoDB endpoint for local dev (e.g. DynamoDB Local)

## Local run/debug (Flask via Docker Compose)

See `projects/api/README.md#local-api-server-flask-via-docker-compose`.
