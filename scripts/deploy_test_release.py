"""Update existing Test items from a verified CI artifact and retain rollback files.

Use a fresh evidence directory per attempt. No create/delete, table writes,
automatic POST retry, or implicit rollback after an uncertain network outcome.
"""
import argparse
import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

from build_test_release import (verify_release, validate_definitions, seal_release, RUNTIME)
from check_test_health import check
from fabric_test_api import Client, FABRIC, WORKSPACE, operation_url
from recovery_common import read_json, write_json, require


class Deployment:
    def __init__(self, client, evidence, timeout=900, sleep=time.sleep, clock=time.monotonic):
        require(timeout > 0, "Positive timeout required")
        require(not evidence.exists(), "Evidence directory exists; inspect previous operation before retrying")
        evidence.mkdir(parents=True)
        self.client, self.evidence, self.timeout = client, evidence, timeout
        self.sleep, self.clock = sleep, clock
        self.events = []

    def log(self, event):
        event["at_utc"] = datetime.now(timezone.utc).isoformat()
        self.events.append(event)
        write_json(self.evidence / "operations.json", self.events)
        print(event.get("step", "operation"), event.get("state", ""), flush=True)

    def request(self, step, url, method="GET", body=None):
        self.log({"step": step, "state": "request_started", "method": method, "url": url})
        status, headers, raw = self.client.request(url, method, body)
        data = json.loads(raw) if raw else {}
        selected = {k.lower(): v for k, v in headers.items() if k.lower() in
                    ("location", "x-ms-operation-id", "retry-after", "x-ms-request-id")}
        # Record accepted identifiers before parsing them; a timeout must not cause a new POST.
        self.log({"step": step, "state": "response_received", "http_status": status, "headers": selected})
        return status, headers, data

    def delay(self, headers, deadline):
        lowered = {k.lower(): v for k, v in headers.items()}
        seconds = max(1, int(lowered.get("retry-after", "5")))
        until = min(self.clock() + seconds, deadline)
        while self.clock() < until:
            self.sleep(min(30, until - self.clock()))

    def fabric_operation(self, step, path, body=None, result=False):
        url = FABRIC + "/v1/workspaces/" + WORKSPACE + path
        status, headers, data = self.request(step, url, "POST", body)
        require(status in (200, 202), "Unexpected Fabric response")
        if status == 200:
            return data
        poll = operation_url(headers)
        self.log({"step": step, "state": "accepted", "poll_url": poll})
        deadline = self.clock() + self.timeout
        while self.clock() < deadline:
            self.delay(headers, deadline)
            if self.clock() >= deadline:
                break
            _, headers, state = self.request(step, poll)
            self.log({"step": step, "state": state.get("status", "unknown")})
            if state.get("status") == "Succeeded":
                return self.request(step + "_result", poll + "/result")[2] if result else state
            if state.get("status") in ("Failed", "Cancelled", "Canceled"):
                write_json(self.evidence / (step + "_failure.json"), state)
                raise RuntimeError("Fabric operation failed: " + step)
        raise TimeoutError("Operation still unresolved; inspect operations.json before retrying: " + poll)

    def refresh(self, model):
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE}/datasets/{model}/refreshes"
        status, headers, data = self.request("refresh", url, "POST",
            {"type": "full", "commitMode": "transactional", "retryCount": 0})
        require(status in (200, 202), "Unexpected refresh response")
        lowered = {k.lower(): v for k, v in headers.items()}
        location = lowered.get("location", "")
        path = urlparse(location).path
        expected = urlparse(url).path + "/"
        require(path.startswith(expected), "Refresh Location targets another model/workspace")
        refresh_id = str(UUID(path[len(expected):]))
        poll = url + "/" + refresh_id
        self.log({"step": "refresh", "state": "accepted", "poll_url": poll})
        deadline = self.clock() + self.timeout
        while self.clock() < deadline:
            self.delay(headers, deadline)
            if self.clock() >= deadline:
                break
            _, headers, data = self.request("refresh_poll", poll)
            write_json(self.evidence / "refresh.json", data)
            state = data.get("status")
            if state == "Completed":
                return data
            if state in ("Failed", "Cancelled", "Canceled", "Disabled"):
                raise RuntimeError("Refresh failed; see refresh.json")
        raise TimeoutError("Refresh unresolved; inspect saved refresh ID before retrying")

    def bind_connection(self, config, step):
        binding = {"id": str(UUID(config["cloud_connection_id"])),
                   "connectivityType": "ShareableCloud",
                   "connectionDetails": {"type": "AzureDataLakeStorage",
                       "path": f"https://onelake.dfs.fabric.microsoft.com/{WORKSPACE}/{config['lakehouse_id']}/"}}
        model = config["semantic_model_id"]
        self.fabric_operation(step, f"/semanticModels/{model}/bindConnection",
                              {"connectionBinding": binding})
        _, _, data = self.request(step + "_verify", FABRIC +
            f"/v1/workspaces/{WORKSPACE}/items/{model}/connections")
        actual = data.get("value", [])
        require(len(actual) == 1 and all(actual[0].get(k) == v for k, v in binding.items()),
                "Model cloud connection does not match the configured Test binding")
        write_json(self.evidence / (step + ".json"), {"status": "passed", "binding": binding})

    def take_ownership(self, model):
        status, _, _ = self.request("take_ownership",
            f"https://api.powerbi.com/v1.0/myorg/groups/{WORKSPACE}/datasets/{model}/Default.TakeOver",
            "POST")
        require(status == 200, "Could not assign Test model ownership to the deployment identity")


def deploy(release, evidence, expected_commit=None, expected_build=None, preflight_only=False,
           client=None, timeout=900):
    require(not evidence.exists(), "Evidence directory exists; inspect previous attempt before retrying")
    try:
        manifest, config = verify_release(release, expected_commit, expected_build)
    except Exception as error:
        evidence.mkdir(parents=True)
        write_json(evidence / "deployment.json", {"status": "failed_before_network", "error": str(error)})
        raise
    runner = Deployment(client or Client(), evidence, timeout)
    summary = {"status": "running", "release": manifest, "preflight_only": preflight_only,
               "model_id": config["semantic_model_id"], "report_id": config["report_id"],
               "identity_type": "Azure CLI current identity; see pipeline service connection for identity provenance"}
    model = read_json(release / "model-update.json")
    report = read_json(release / "report-update.json")
    model_path = "/semanticModels/" + config["semantic_model_id"]
    report_path = "/reports/" + config["report_id"]
    try:
        # Fail before any update if items do not exist or the unattended identity cannot query DAX.
        for suffix, expected_type in [(model_path, "SemanticModel"), (report_path, "Report")]:
            _, _, item = runner.request("target_inventory", FABRIC + "/v1/workspaces/" + WORKSPACE + suffix)
            require(item["id"] == suffix.rsplit("/", 1)[-1] and item["type"] == expected_type,
                    "Unexpected existing target item")
        check(evidence / "health_before.json", release / "config/environments/test.json", runner.client)
        runner.take_ownership(config["semantic_model_id"])
        # Prove this identity can bind the selected connection before changing definitions.
        # updateDefinition can clear the mapping even when the OneLake URL is unchanged.
        runner.bind_connection(config, "preflight_connection")
        prior_model = runner.fabric_operation("capture_model", model_path + "/getDefinition", result=True)
        prior_report = runner.fabric_operation("capture_report", report_path + "/getDefinition", result=True)
        for body in (prior_model, prior_report):
            body["definition"]["parts"] = [p for p in body["definition"]["parts"] if p["path"] != ".platform"]
        validate_definitions(prior_model, prior_report, config)
        rollback = evidence / "rollback"
        (rollback / "config/environments").mkdir(parents=True)
        (rollback / "scripts").mkdir()
        write_json(rollback / "model-update.json", prior_model)
        write_json(rollback / "report-update.json", prior_report)
        write_json(rollback / "config/environments/test.json", config)
        for name in RUNTIME:
            shutil.copyfile(release / "scripts" / name, rollback / "scripts" / name)
        shutil.copyfile(release / "requirements-cd.txt", rollback / "requirements-cd.txt")
        seal_release(rollback, manifest["commit_sha"], "capture-before-" + manifest["build_id"], manifest["source_branch"])
        # This is a live capture; the previous deployment's source commit may be unknown.
        capture = read_json(rollback / "manifest.json")
        capture["provenance"] = "Live definitions captured before this deployment; commit_sha identifies capture tooling, not the prior item source."
        write_json(rollback / "manifest.json", capture)
        verify_release(rollback)
        if preflight_only:
            summary["status"] = "preflight_passed_no_updates"
        else:
            runner.fabric_operation("update_model", model_path + "/updateDefinition", model)
            runner.bind_connection(config, "restore_connection")
            live = runner.fabric_operation("verify_model", model_path + "/getDefinition", result=True)
            validate_definitions(live, report, config)
            write_json(evidence / "model_binding.json", {"status": "passed", "workspace_id": WORKSPACE,
                "lakehouse_id": config["lakehouse_id"], "gold_run_id": config["gold_run_id"]})
            runner.refresh(config["semantic_model_id"])
            # Check model KPI before publishing report; current report must still target the same model.
            check(evidence / "health_model.json", release / "config/environments/test.json", runner.client)
            runner.fabric_operation("update_report", report_path + "/updateDefinition", report)
            check(evidence / "health_after.json", release / "config/environments/test.json", runner.client)
            summary["status"] = "passed"
    except Exception as error:
        summary.update(status="failed", error=str(error),
                       recovery="Inspect operation IDs first. A captured rollback is retained when available; no automatic retry or rollback was attempted.")
        raise
    finally:
        write_json(evidence / "deployment.json", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--expected-commit")
    parser.add_argument("--expected-build")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    print(json.dumps(deploy(args.release, args.evidence, args.expected_commit,
          args.expected_build, args.preflight_only, timeout=args.timeout), indent=2))
