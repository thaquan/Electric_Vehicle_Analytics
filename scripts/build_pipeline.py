"""Build PL_EV_E2E for the existing notebook IDs in WS_EV_Analytics."""
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def expression(value):
    return {"value": value, "type": "Expression"}


def build():
    config = json.loads((ROOT / "metadata/fabric_workspace.json").read_text())
    pipeline_id = expression("@pipeline().RunId")
    silver_id = expression("@json(activity('Build_Silver').output.result.exitValue).run_id")
    gold_id = expression("@json(activity('Build_Gold').output.result.exitValue).run_id")
    stages = [
        ("Check_Bronze", "silver_notebook_id", {"run_mode": "validate_only"}),
        ("Build_Silver", "silver_notebook_id", {"run_mode": "publish"}),
        ("Validate_Silver", "gold_notebook_id", {"run_mode": "verify_silver", "silver_run_id": silver_id}),
        ("Build_Gold", "gold_notebook_id", {"run_mode": "publish", "silver_run_id": silver_id}),
        ("Validate_Gold", "gold_notebook_id", {"run_mode": "verify_gold", "silver_run_id": silver_id, "gold_run_id": gold_id}),
    ]
    activities = []
    previous = None
    for name, notebook, parameters in stages:
        parameters = {"pipeline_run_id": pipeline_id, **parameters}
        activities.append({"name": name, "type": "TridentNotebook",
            "dependsOn": [{"activity": previous, "dependencyConditions": ["Succeeded"]}] if previous else [],
            "policy": {"timeout": "0.01:00:00", "retry": 0, "retryIntervalInSeconds": 30, "secureInput": False, "secureOutput": False},
            "typeProperties": {"notebookId": config[notebook], "workspaceId": config["workspace_id"],
                "parameters": {key: {"value": value, "type": "string"} for key, value in parameters.items()}}})
        previous = name
    folder = ROOT / "PL_EV_E2E.DataPipeline"
    folder.mkdir(exist_ok=True)
    platform = folder / ".platform"
    if not platform.exists():
        platform.write_text(json.dumps({"$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": "DataPipeline", "displayName": "PL_EV_E2E", "description": "On-demand Bronze checks, Silver publication, Gold publication and independent verification."},
            "config": {"version": "2.0", "logicalId": str(uuid.uuid4())}}, indent=2) + "\n", encoding="utf-8")
    payload = {"properties": {"description": "Check Bronze -> Build Silver -> Validate Silver -> Build Gold -> Validate Gold. Stop on any failure. Snapshot contract v2.", "activities": activities}}
    (folder / "pipeline-content.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("Built PL_EV_E2E with five success-dependent activities; schedule omitted.")


if __name__ == "__main__":
    build()
