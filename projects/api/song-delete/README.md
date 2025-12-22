# Song Delete Lambda Handler

Lambda function for the `DELETE /songs/{id}` API Gateway endpoint. Deletes a song record from the shared DynamoDB music table.

## Environment Variables

- `MUSIC_TABLE_NAME`: DynamoDB single-table name (set by Terraform)
- `DYNAMODB_ENDPOINT_URL` (optional): Override DynamoDB endpoint for local dev (e.g. DynamoDB Local / LocalStack)

## Deployment

Package and deploy via the repo tasks:

```bash
task api:package:song-delete
task api:deploy:song-delete
```

## Local run/debug (Flask via Docker Compose)

See `projects/api/README.md#local-api-server-flask-via-docker-compose`.
