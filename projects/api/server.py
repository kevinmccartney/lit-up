from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from flask import Flask, Request, Response, request
from flask_cors import CORS  # type: ignore[import]

ROOT = Path(__file__).resolve().parent


def _load_handler(module_name: str, relative_path: str):
    """Load a handler.py from a lambda directory with dashes in its name."""
    module_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {relative_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.handler


# Import Lambda handlers as regular functions (directories use hyphens)
config_post_handler = _load_handler("config_post_handler", "config-post/handler.py")
config_get_handler = _load_handler("config_get_handler", "config-get/handler.py")
config_delete_handler = _load_handler(
    "config_delete_handler", "config-delete/handler.py"
)
config_list_handler = _load_handler("config_list_handler", "config-list/handler.py")
config_patch_handler = _load_handler("config_patch_handler", "config-patch/handler.py")


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


def _lambda_event(
    req: Request, path_params: dict[str, str] | None = None
) -> dict[str, Any]:
    """Convert a Flask request into a minimal API Gateway proxy event."""
    body_bytes = req.get_data()
    body = body_bytes.decode() if body_bytes else None
    qs = req.args.to_dict()
    headers = dict(req.headers)

    return {
        "httpMethod": req.method,
        "path": req.path,
        "headers": headers,
        "multiValueHeaders": None,
        "queryStringParameters": qs or None,
        "multiValueQueryStringParameters": None,
        "pathParameters": path_params or None,
        "stageVariables": None,
        "requestContext": {
            "resourcePath": req.path,
            "httpMethod": req.method,
            "path": req.path,
        },
        "body": body,
        "isBase64Encoded": False,
    }


def _to_flask_response(result: dict[str, Any]) -> Response:
    return Response(
        response=result.get("body", ""),
        status=result.get("statusCode", 500),
        headers=result.get("headers", {}),
        mimetype=result.get("headers", {}).get("content-type", "application/json"),
    )


@app.post("/configs")
def post_config() -> Response:
    event = _lambda_event(request)
    result = config_post_handler(event, None)
    return _to_flask_response(result)


@app.get("/configs/<config_id>")
def get_config(config_id: str) -> Response:
    event = _lambda_event(request, path_params={"id": config_id})
    result = config_get_handler(event, None)
    return _to_flask_response(result)


@app.delete("/configs/<config_id>")
def delete_config(config_id: str) -> Response:
    event = _lambda_event(request, path_params={"id": config_id})
    result = config_delete_handler(event, None)
    return _to_flask_response(result)


@app.get("/configs")
def list_configs() -> Response:
    event = _lambda_event(request)
    result = config_list_handler(event, None)
    return _to_flask_response(result)


@app.patch("/configs/<config_id>")
def patch_config(config_id: str) -> Response:
    event = _lambda_event(request, path_params={"id": config_id})
    result = config_patch_handler(event, None)
    return _to_flask_response(result)


# Run the Flask app when executed directly or via debugpy
# This ensures all routes are registered before the server starts
if __name__ == "__main__" or __name__ == "__mp_main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
