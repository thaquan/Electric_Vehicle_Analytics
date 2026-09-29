"""Future recovery step: create a NEW Fabric item from a prepared definition.

Uses an existing Azure CLI user login. Never prints or persists the access token.
Does not run during packaging. No update/delete or automatic POST retries.
"""
import argparse
import base64
import json
from pathlib import Path
import shutil
import subprocess
import time
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import UUID

from recovery_common import read_json, require, validate_config, write_json

RESOURCE = "https://api.fabric.microsoft.com"


def check_operation_url(url):
    parsed = urlparse(url)
    require(parsed.scheme == "https" and parsed.netloc == "api.fabric.microsoft.com"
            and parsed.path.startswith("/v1/operations/"), "Unexpected Fabric operation URL")
    return url


def operation_url_from_headers(headers):
    """Poll the public endpoint even when Fabric returns a regional Location."""
    operation_id = headers.get("x-ms-operation-id")
    if operation_id:
        operation_id = str(UUID(operation_id))
        return check_operation_url(f"{RESOURCE}/v1/operations/{operation_id}")
    return check_operation_url(headers["Location"])


def check_payload(kind, body, config):
    validate_config(config, report=kind == "report")
    name = config["semantic_model_name" if kind == "model" else "report_name"]
    require(body["displayName"] == name, "Prepared display name differs from config")
    parts = body["definition"]["parts"]
    decoded = {p["path"]: base64.b64decode(p["payload"], validate=True) for p in parts}
    require(len(decoded) == len(parts), "Duplicate definition parts")
    if kind == "model":
        expected_url = f"https://onelake.dfs.fabric.microsoft.com/{config['workspace_id']}/{config['lakehouse_id']}"
        require(expected_url in decoded["definition/expressions.tmdl"].decode("utf-8"), "Prepared model targets a different lakehouse")
    else:
        binding = json.loads(decoded["definition.pbir"])
        require("semanticmodelid=" + config["semantic_model_id"] in binding["datasetReference"]["byConnection"]["connectionString"], "Prepared report targets a different model")


def create(kind, prepared, config, result_path):
    validate_config(config, report=kind == "report")
    require(not result_path.exists(), "Use a new result filename; inspect any previous create before retrying")
    filename = "create_semantic_model.json" if kind == "model" else "create_report.json"
    body = read_json(prepared / filename)
    check_payload(kind, body, config)
    command = shutil.which("az")
    require(command is not None, "Install Azure CLI and run az login first")
    token_result = subprocess.run([command, "account", "get-access-token", "--resource", RESOURCE,
                                  "--query", "accessToken", "--output", "tsv"], capture_output=True, text=True, check=True)
    token = token_result.stdout.strip()
    require(bool(token), "Azure CLI did not return a Fabric token")

    def request(url, method="GET", payload=None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = Request(url, data=data, method=method,
                      headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
        with urlopen(req, timeout=120) as response:
            raw = response.read()
            return response.status, response.headers, json.loads(raw) if raw else {}

    suffix = "semanticModels" if kind == "model" else "reports"
    endpoint = f"{RESOURCE}/v1/workspaces/{config['workspace_id']}/{suffix}"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    # Preserve an attempt record even when a network timeout leaves the result unknown.
    write_json(result_path, {"status": "create_attempt_started", "endpoint": endpoint, "display_name": body["displayName"]})
    code, headers, result = request(endpoint, "POST", body)
    if code == 202:
        # Preserve server identifiers before validation so an accepted create is
        # recoverable even when its response headers are unexpected.
        write_json(result_path, {"status": "accepted", "endpoint": endpoint,
                                "operation_id": headers.get("x-ms-operation-id"),
                                "location": headers.get("Location")})
        operation = operation_url_from_headers(headers)
        write_json(result_path, {"status": "accepted", "operation_url": operation, "endpoint": endpoint})
        deadline = time.monotonic() + 900
        while time.monotonic() < deadline:
            # Retry-After is seconds for this Fabric API.
            delay = max(1, int(headers.get("Retry-After", "5")))
            wait_until = time.monotonic() + delay
            while time.monotonic() < wait_until:
                time.sleep(min(60, max(0, wait_until - time.monotonic())))
            code, headers, state = request(operation)
            if state.get("status") == "Succeeded":
                _, _, result = request(check_operation_url(operation.rstrip("/") + "/result"))
                break
            if state.get("status") in ("Failed", "Cancelled"):
                write_json(result_path, {"status": "failed", "operation_url": operation, "details": state})
                raise RuntimeError("Fabric create failed; see result file")
        else:
            raise TimeoutError("Operation still pending; poll the saved operation URL before any new create")
    else:
        require(code == 201, "Unexpected create response")
    require(bool(result.get("id")), "Create completed without an item ID; inspect Fabric before retrying")
    require(result.get("workspaceId", config["workspace_id"]).lower() == config["workspace_id"].lower(), "Created item workspace mismatch")
    write_json(result_path, {"status": "created", "item": result, "endpoint": endpoint})
    return {"status": "created", "id": result["id"], "result": str(result_path)}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("kind", choices=["model", "report"])
    p.add_argument("--prepared", type=Path, required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--result", type=Path, required=True)
    a = p.parse_args()
    try:
        print(json.dumps(create(a.kind, a.prepared, read_json(a.config), a.result), indent=2))
    except HTTPError as error:
        raise SystemExit(f"Fabric HTTP {error.code}: {error.reason}. Check the saved attempt and Fabric workspace before retrying.")
