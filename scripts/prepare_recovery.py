"""Prepare new model/report definitions and REST request bodies, without network calls."""
import argparse
import base64
import json
import re
import shutil
from pathlib import Path
from uuid import uuid4

from recovery_common import (SOURCE_MODEL, SOURCE_WORKSPACE, SOURCE_LAKEHOUSE,
                             check_snapshot, identifier, read_json, require, validate_config, write_json)
from star_schema import DIMENSIONS
from star_sql import star_queries

PROJECT = Path(__file__).resolve().parents[1]


def copy_artifact(source, target):
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(".pbi", "__pycache__", "*.pyc", "localSettings.json"))


def new_platform(folder, name):
    platform = read_json(folder / ".platform")
    platform["metadata"]["displayName"] = name
    platform["config"]["logicalId"] = str(uuid4())
    write_json(folder / ".platform", platform)


def request_body(folder, name):
    return {"displayName": name, "description": "Recovery copy of verified EV Gold v2 snapshot.",
            "definition": {"parts": [
                {"path": p.relative_to(folder).as_posix(),
                 "payload": base64.b64encode(p.read_bytes()).decode("ascii"), "payloadType": "InlineBase64"}
                for p in sorted(folder.rglob("*")) if p.is_file()]}}


def prepare_model(project, snapshot, config, output):
    validate_config(config)
    manifest = check_snapshot(snapshot)
    require(not output.exists(), "Use a new output directory")
    output.mkdir(parents=True)
    name = config["semantic_model_name"]
    folder = output / (name + ".SemanticModel")
    copy_artifact(project / "SM_EV_Analytics.SemanticModel", folder)
    new_platform(folder, name)
    definition = folder / "definition"
    expression = definition / "expressions.tmdl"
    text = expression.read_text(encoding="utf-8")
    source_url = f"https://onelake.dfs.fabric.microsoft.com/{SOURCE_WORKSPACE}/{SOURCE_LAKEHOUSE}"
    require(text.count(source_url) == 1, "Expected one Gold source expression")
    target_url = f"https://onelake.dfs.fabric.microsoft.com/{config['workspace_id']}/{config['lakehouse_id']}"
    expression.write_text(text.replace(source_url, target_url), encoding="utf-8")
    database = definition / "database.tmdl"
    text = database.read_text(encoding="utf-8")
    text, n = re.subn(r"(?m)^database(?: SM_EV_Analytics)?$", "database " + name, text)
    require(n == 1, "Unexpected database declaration")
    text, n = re.subn(r"(?m)^\tid: " + re.escape(SOURCE_MODEL) + r"\n", "", text)
    require(n <= 1, "Unexpected duplicate source database IDs")
    database.write_text(text, encoding="utf-8")
    model = definition / "model.tmdl"
    text, n = re.subn(r"(?m)^model SM_EV_Analytics$", "model " + name, model.read_text(encoding="utf-8"))
    require(n == 1, "Unexpected model declaration")
    model.write_text(text, encoding="utf-8")
    expected_entities = {t["restore_table"] for t in manifest["tables"] if t["role"].startswith(("fact_", "dim_"))}
    entities = set()
    for table in sorted((definition / "tables").glob("*.tmdl")):
        text = table.read_text(encoding="utf-8")
        require(text.count("mode: directLake") == 1, "Expected one Direct Lake partition")
        names = re.findall(r"(?m)^\s+entityName: (\w+)$", text)
        require(len(names) == 1, "Expected one table entity")
        entities.add(names[0])
        text = re.sub(r"(?m)^\t\t\tschemaName:.*\n", "", text)
        if config["lakehouse_schema"]:
            text = text.replace("\t\t\texpressionSource: GoldLakehouse", "\t\t\tschemaName: " + config["lakehouse_schema"] + "\n\t\t\texpressionSource: GoldLakehouse")
        table.write_text(text, encoding="utf-8")
    require(entities == expected_entities, "Model partitions do not match the snapshot")
    for file in definition.rglob("*.tmdl"):
        text = file.read_text(encoding="utf-8")
        require(not any(value in text for value in (SOURCE_MODEL, SOURCE_WORKSPACE, SOURCE_LAKEHOUSE)), "Source connection remains in recovery model")
    write_json(output / "create_semantic_model.json", request_body(folder, name))
    # Gold-only reconciliation; the original SQL also references Silver.
    schema = config["lakehouse_schema"] or "dbo"
    names = {t["role"]: schema + "." + identifier(t["restore_table"]) for t in manifest["tables"]}
    spec = read_json(snapshot / "evidence/gold_spec.json")
    queries = star_queries(names, DIMENSIONS, spec["segments"])
    statements = ["-- Recovery lakehouse SQL endpoint only. Read-only, optional; no Silver dependency.",
                  "-- Expected KPI: 668665 / 116779 / 551886; 35 segment groups.", queries["kpi"] + ";", queries["segments"] + ";"]
    for role, keys in manifest["primary_keys"].items():
        columns = ", ".join(keys)
        nulls = " OR ".join(k + " IS NULL" for k in keys)
        statements.append(f"SELECT {columns}, COUNT(*) AS n FROM {names[role]} GROUP BY {columns} HAVING COUNT(*) > 1 OR {nulls};")
    for dim in DIMENSIONS:
        key = dim["key"]
        statements.append(f"SELECT '{dim['role']}' AS dimension_name, COUNT(*) AS orphan_count FROM {names['fact_ev_purchase_intent']} f LEFT JOIN {names[dim['role']]} d ON f.{key}=d.{key} WHERE d.{key} IS NULL;")
    (output / "recovery_gold_checks.sql").write_text("\n\n".join(statements) + "\n", encoding="utf-8")
    write_json(output / "prepared.json", {"status": "prepared_not_deployed", "workspace_id": config["workspace_id"],
               "endpoint": f"https://api.fabric.microsoft.com/v1/workspaces/{config['workspace_id']}/semanticModels",
               "method": "POST", "request_body": "create_semantic_model.json", "tables": 6, "relationships": 5})
    return folder


def prepare_report(project, config, output):
    validate_config(config, report=True)
    require(not output.exists(), "Use a new output directory")
    output.mkdir(parents=True)
    name = config["report_name"]
    folder = output / (name + ".Report")
    copy_artifact(project / "RPT_EV_Analytics.Report", folder)
    new_platform(folder, name)
    binding = read_json(folder / "definition.pbir")
    binding["datasetReference"] = {"byConnection": {"connectionString": (
        f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{config['workspace_name']};"
        f"initial catalog={config['semantic_model_name']};access mode=readonly;"
        f"integrated security=ClaimsToken;semanticmodelid={config['semantic_model_id']}"
    )}}
    write_json(folder / "definition.pbir", binding)
    pbip = read_json(project / "RPT_EV_Analytics.pbip")
    pbip["artifacts"] = [{"report": {"path": folder.name}}]
    write_json(output / (name + ".pbip"), pbip)
    write_json(output / "create_report.json", request_body(folder, name))
    write_json(output / "prepared.json", {"status": "prepared_not_published", "workspace_id": config["workspace_id"],
               "semantic_model_id": config["semantic_model_id"],
               "endpoint": f"https://api.fabric.microsoft.com/v1/workspaces/{config['workspace_id']}/reports",
               "method": "POST", "request_body": "create_report.json"})
    return folder


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("kind", choices=["model", "report"])
    p.add_argument("--project", type=Path, default=PROJECT)
    p.add_argument("--snapshot", type=Path, default=Path("snapshot"))
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    config = read_json(a.config)
    folder = prepare_model(a.project, a.snapshot, config, a.output) if a.kind == "model" else prepare_report(a.project, config, a.output)
    print(json.dumps({"status": "prepared_only", "artifact": str(folder.resolve())}, indent=2))


if __name__ == "__main__":
    main()
