# Local Lambda running + debugging (SAM)

This folder provides a local dev loop for the Python Lambdas using **AWS SAM** running entirely in Docker Compose.

## Prerequisites

- Docker and Docker Compose installed and running
- No need to install `sam` CLI or Python dependencies on your host—everything runs in containers

## Quick Start

Start the entire local development stack:

```bash
task up
```

This automatically starts:

- **DynamoDB Local** (in-memory) on `:8000`
- **DynamoDB Admin UI** on `:8001` (web interface for browsing tables)
- **SAM CLI + API Gateway/Lambda emulation** on `:3001`
- **DynamoDB table initialization** (creates `lit-up-dev-configs` table if it doesn't exist)

## Endpoints

- **API Gateway**: `http://127.0.0.1:3001/config` (POST)
- **DynamoDB Local**: `http://127.0.0.1:8000`
- **DynamoDB Admin UI**: `http://127.0.0.1:8001`

## Testing the API

```bash
curl -sS -X POST "http://127.0.0.1:3001/config?version=v1" \
  -H "content-type: application/json" \
  --data @<(python -c 'import json; import pathlib; print(json.loads(pathlib.Path("projects/api/local/events/config-post.apigw.json").read_text())["body"])')
```

## Stopping the Stack

```bash
task down
```

## Debugging (step-through in Cursor/VS Code)

**Debugging is enabled by default** when running locally. Each Lambda function has its own debug port:

- **config-post**: Port `5890`

To add debugging for additional Lambda functions:

1. Add the debug port to the root `docker-compose.local.yml` under the `sam` service `ports` section:

   ```yaml
   - '5891:5891' # For your next lambda
   ```

2. Add debugpy configuration to `env.docker.json` for the new function:

   ```json
   "YourNewFunction": {
     ...
     "DEBUGPY_ENABLE": "1",
     "DEBUGPY_WAIT_FOR_CLIENT": "1",
     "DEBUGPY_HOST": "0.0.0.0",
     "DEBUGPY_PORT": "5891"
   }
   ```

3. Update `.vscode/launch.json` with a new attach configuration for the new port.

Then attach your debugger using the `.vscode/launch.json` config **Attach to SAM (config-post)**.

**Note**: The container path is `/var/task` (mapped in `launch.json`). The Lambda will wait for debugger attach when `DEBUGPY_WAIT_FOR_CLIENT=1` is set in the environment.

## How It Works

- The `sam` service runs SAM CLI inside a container, mounting your code and the Docker socket
- SAM builds and runs Lambda functions in separate containers on the `litup_local` network
- Lambdas connect to DynamoDB via the service name `http://dynamodb:8000` (container-to-container)
- The `dynamodb-init` service automatically creates the required table on startup if it doesn't exist
- All services share the `litup_local` Docker network for inter-container communication
