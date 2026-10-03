"""Check Test report binding, latest refresh, and live DAX KPI.

Writes evidence and returns a nonzero exit code on failure. No messages are sent.
Intended for on-demand operation or a future scheduled Azure DevOps job.
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from fabric_test_api import Client, WORKSPACE

ROOT = Path(__file__).resolve().parents[1]


def check(output, config_path=None, client=None):
    config = json.loads((config_path or ROOT / "config/environments/test.json").read_text())
    if config["workspace_id"] != WORKSPACE:
        raise ValueError("Unexpected Test workspace")
    client = client or Client()
    base = "https://api.powerbi.com/v1.0/myorg/groups/" + WORKSPACE
    result = {"status": "running", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "workspace_id": WORKSPACE, "semantic_model_id": config["semantic_model_id"],
              "report_id": config["report_id"], "checks": {}}
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        _, _, raw = client.request(base + "/reports/" + config["report_id"])
        report = json.loads(raw)
        if report["datasetId"] != config["semantic_model_id"] or report.get("datasetWorkspaceId", WORKSPACE) != WORKSPACE:
            raise ValueError("Report binds to the wrong model/workspace")
        result["checks"]["report_binding"] = "passed"
        _, _, raw = client.request(base + "/datasets/" + config["semantic_model_id"] + "/refreshes?$top=1")
        refreshes = json.loads(raw)["value"]
        if not refreshes or refreshes[0]["status"] != "Completed":
            raise ValueError("Latest model refresh is missing, failed, or not completed")
        result["latest_refresh"] = refreshes[0]
        result["checks"]["latest_refresh"] = "passed"
        query = 'EVALUATE ROW("respondents",[Respondents],"yes",[Intending to Buy EV],"no",[Not Intending to Buy EV])'
        backend = os.environ.get("EV_DAX_API", "json")
        result["dax_api"] = backend
        if backend == "arrow":
            from dax_query import arrow_rows
            _, _, raw = client.request("https://api.powerbi.com/v1.0/myorg/datasets/" +
                config["semantic_model_id"] + "/executeDaxQueries", "POST",
                {"query": query, "queryTimeout": 120, "resultSetRowCountLimit": 10})
            rows = arrow_rows(raw)
        elif backend == "json":
            _, _, raw = client.request(base + "/datasets/" + config["semantic_model_id"] + "/executeQueries",
                                      "POST", {"queries": [{"query": query}]})
            data = json.loads(raw)
            if data.get("error") or any(r.get("error") for r in data.get("results", [])):
                raise ValueError("DAX returned an error")
            rows = data["results"][0]["tables"][0]["rows"]
        else:
            raise ValueError("Unsupported DAX API")
        if len(rows) != 1:
            raise ValueError("Expected one KPI row")
        actual = {k: rows[0]["[" + k + "]"] for k in config["expected_kpi"]}
        result["actual_kpi"] = actual
        if actual != config["expected_kpi"]:
            raise ValueError("Live KPI differs from pinned snapshot")
        result["checks"]["dax_kpi"] = "passed"
        result["status"] = "passed"
    except Exception as error:
        result.update(status="failed", error=str(error))
        raise
    finally:
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    check(parser.parse_args().output)
