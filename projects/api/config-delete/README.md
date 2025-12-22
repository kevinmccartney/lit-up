# Config Delete Lambda Handler

Lambda function for the `DELETE /configs/{id}` API Gateway endpoint. Deletes a saved playlist config from DynamoDB by `id`.

## Deployment

This Lambda is deployed independently from the infrastructure.

After Terraform creates the function, the recommended flow is:

```bash
task api:package:config-delete
task api:deploy:config-delete
```

## Environment Variables

The Lambda expects:

- `MUSIC_TABLE_NAME`: DynamoDB single-table name (set by Terraform)
- `DYNAMODB_ENDPOINT_URL` (optional): Override DynamoDB endpoint for local dev (e.g. DynamoDB Local)

## Local run/debug (Flask via Docker Compose)

See `projects/api/README.md#local-api-server-flask-via-docker-compose`.
