# Config Post Lambda Handler

Lambda function for the `POST /config` API Gateway endpoint. Reads playlist configs from DynamoDB.

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

- `CONFIG_TABLE_NAME`: DynamoDB table name (set by Terraform)
- `DYNAMODB_ENDPOINT_URL` (optional): Override DynamoDB endpoint for local dev (e.g. DynamoDB Local)

## Testing

Test locally with a mock event:

```python
event = {}
result = handler(event, None)
print(result)
```

## Local run/debug (SAM)

See `projects/api/local/README.md`.

Note: SAM local builds install runtime deps from `requirements.txt` in this folder.
