"""Small authenticated client scoped to the EV Test workspace.

Uses the existing Azure CLI login without printing or saving tokens. Mutating
requests are never automatically retried. Keep returned operation/job IDs.
"""
import json
import shutil
import subprocess
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlparse, unquote
from uuid import UUID

WORKSPACE = "27873d0c-580a-4963-9e25-5846948f1c5d"
FABRIC = "https://api.fabric.microsoft.com"


class Client:
    def __init__(self):
        self.tokens = {}

    def token(self, resource):
        if resource not in self.tokens:
            result = subprocess.run(
                [shutil.which("az"), "account", "get-access-token", "--resource",
                 resource, "--query", "accessToken", "-o", "tsv"],
                capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError("Azure CLI authentication failed; renew the existing login.")
            self.tokens[resource] = result.stdout.strip()
        return self.tokens[resource]

    def request(self, url, method="GET", body=None, headers=None):
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
            raise ValueError("HTTPS required")
        if any(segment in (".", "..") for segment in unquote(parsed.path).split("/")):
            raise ValueError("Path traversal is forbidden")
        if parsed.hostname == "api.fabric.microsoft.com":
            allowed = parsed.path.startswith(f"/v1/workspaces/{WORKSPACE}/")
            allowed |= parsed.path == f"/v1/workspaces/{WORKSPACE}"
            allowed |= method == "GET" and parsed.path.startswith("/v1/operations/")
            resource = FABRIC
        elif parsed.hostname == "api.powerbi.com":
            allowed = parsed.path.startswith(f"/v1.0/myorg/groups/{WORKSPACE}/")
            # Modern DAX API has no workspace segment. Restrict it to the one
            # existing Test model and to query POSTs only.
            allowed |= method == "POST" and parsed.path == "/v1.0/myorg/datasets/a97a9cc1-eaac-4007-b8ad-c146ac1776c5/executeDaxQueries"
            resource = "https://analysis.windows.net/powerbi/api"
        elif parsed.hostname == "onelake.blob.fabric.microsoft.com":
            allowed = parsed.path.startswith(f"/{WORKSPACE}/")
            resource = "https://storage.azure.com/"
        else:
            allowed = False
        if not allowed:
            raise ValueError("Request outside the Test workspace")
        data = body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else None
        request_headers = {"Authorization": "Bearer " + self.token(resource),
                           "Content-Type": "application/json"}
        request_headers.update(headers or {})
        try:
            with urlopen(Request(url, data=data, method=method, headers=request_headers), timeout=120) as response:
                raw = response.read()
                return response.status, dict(response.headers), raw
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {error.code}: {detail}") from None

    def api(self, path, method="GET", body=None):
        code, headers, raw = self.request(FABRIC + "/v1/workspaces/" + WORKSPACE + path, method, body)
        return code, headers, json.loads(raw) if raw else {}


def operation_url(headers):
    lowered = {k.lower(): v for k, v in headers.items()}
    operation = lowered.get("x-ms-operation-id")
    if operation:
        return FABRIC + "/v1/operations/" + str(UUID(operation))
    raise ValueError("Accepted operation has no operation ID; inspect saved headers before retrying")


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Workspace-relative API path, or /v1/operations/ ID for polling")
    parser.add_argument("--method", default="GET", choices=["GET", "POST"])
    parser.add_argument("--body", type=Path)
    parser.add_argument("--powerbi", action="store_true")
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    if args.method != "GET" and args.result.exists():
        raise SystemExit("Inspect the existing attempt before retrying; choose a new journal only for a new operation")
    args.result.parent.mkdir(parents=True, exist_ok=True)
    record = {"status": "request_started", "method": args.method, "path": args.path}
    args.result.write_text(json.dumps(record, indent=2))
    client = Client()
    payload = json.loads(args.body.read_text(encoding="utf-8")) if args.body else None
    url = FABRIC + args.path if args.path.startswith("/v1/operations/") else FABRIC + "/v1/workspaces/" + WORKSPACE + args.path
    if args.powerbi:
        url = "https://api.powerbi.com/v1.0/myorg/groups/" + WORKSPACE + args.path
    code, headers, raw = client.request(url, args.method, payload)
    record.update(status="response_received", http_status=code,
                  headers={k: v for k, v in headers.items() if k.lower() in
                           ["location", "x-ms-operation-id", "retry-after"]},
                  body=json.loads(raw) if raw else {})
    args.result.write_text(json.dumps(record, indent=2))
    display = dict(record)
    if isinstance(display["body"], dict) and "definition" in display["body"]:
        display["body"] = {"definition_saved": str(args.result)}
    print(json.dumps(display, indent=2))
