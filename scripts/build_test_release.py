"""Build a deterministic Test model/report release without a local data snapshot.

Only the already verified Gold run is supported. This packages definitions, not
data, and does not claim to revalidate Parquet or execute Spark.
"""
import argparse
import base64
import hashlib
import json
import re
import shutil
from pathlib import Path, PurePosixPath
from uuid import UUID

from fabric_test_api import WORKSPACE
from recovery_common import (SOURCE_WORKSPACE, SOURCE_LAKEHOUSE, SOURCE_MODEL,
                             GOLD_RUN, read_json, require, write_json, validate_config)

ROOT = Path(__file__).resolve().parents[1]
TARGET_MODEL = "a97a9cc1-eaac-4007-b8ad-c146ac1776c5"
TARGET_REPORT = "b7d65039-0413-4ecc-9f7f-33f0098c9cc0"
TARGET_LAKEHOUSE = "970801bb-ffc3-4c5a-b25d-a940a5fd697e"
ROLES = {"fact_ev_purchase_intent", "dim_demographics", "dim_income", "dim_mobility",
         "dim_charging", "dim_attitude_incentive"}
RUNTIME = ["build_test_release.py", "deploy_test_release.py", "fabric_test_api.py",
           "recovery_common.py", "check_test_health.py"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_target(config):
    validate_config(config, report=True)
    require(config.get("environment") == "test", "Only Test deployments are supported")
    for key, value in [("workspace_id", WORKSPACE), ("lakehouse_id", TARGET_LAKEHOUSE),
                       ("semantic_model_id", TARGET_MODEL), ("report_id", TARGET_REPORT)]:
        require(config.get(key) == value, "Unexpected Test target: " + key)
    require(config["expected_kpi"] == {"respondents": 668665, "yes": 116779, "no": 551886},
            "Unexpected KPI for pinned Gold run")


def decode_parts(body):
    result = {}
    for part in body["definition"]["parts"]:
        path = part["path"]
        require(path not in result, "Duplicate definition part")
        require(not PurePosixPath(path).is_absolute() and ".." not in PurePosixPath(path).parts
                and "\\" not in path and ":" not in path, "Unsafe definition path")
        require(part["payloadType"] == "InlineBase64", "InlineBase64 required")
        result[path] = base64.b64decode(part["payload"], validate=True)
    return result


def validate_definitions(model, report, config):
    validate_target(config)
    parts = decode_parts(model)
    texts = {k: v.decode("utf-8") for k, v in parts.items() if k.endswith(".tmdl")}
    text = "\n".join(texts.values())
    require(not any(value in text for value in (SOURCE_WORKSPACE, SOURCE_LAKEHOUSE, SOURCE_MODEL)),
            "Dev reference remains in model")
    expected_url = f"https://onelake.dfs.fabric.microsoft.com/{WORKSPACE}/{config['lakehouse_id']}"
    urls = re.findall(r'AzureStorage.DataLake\("([^\"]+)"', texts["definition/expressions.tmdl"])
    require(urls == [expected_url], "Unexpected OneLake source")
    tables = [v for k, v in texts.items() if k.startswith("definition/tables/")]
    require(len(tables) == 6, "Expected six model tables")
    entities = []
    for table in tables:
        require(table.count("mode: directLake") == 1, "Expected Direct Lake partition")
        names = re.findall(r"(?m)^\s+entityName: (\w+)\s*$", table)
        require(len(names) == 1, "Expected one entity per table")
        entities.extend(names)
        schemas = re.findall(r"(?m)^\s+schemaName: (\w+)\s*$", table)
        require(schemas == ([config["lakehouse_schema"]] if config["lakehouse_schema"] else []),
                "Wrong partition schema")
    require(set(entities) == {role + "_" + GOLD_RUN.lower() for role in ROLES}, "Mixed or wrong Gold run")
    require(len(re.findall(r"(?m)^relationship ", text)) == 5, "Expected five relationships")
    require(len(re.findall(r"(?m)^\s+measure ", text)) == 12, "Expected 12 measures")
    binding = json.loads(decode_parts(report)["definition.pbir"])["datasetReference"]
    require(set(binding) == {"byConnection"}, "Report must bind by connection")
    connection = binding["byConnection"]["connectionString"]
    fields = dict(piece.split("=", 1) for piece in connection.split(";") if piece)
    require(fields.get("semanticmodelid") == config["semantic_model_id"], "Wrong report model")
    require(fields.get("Data Source") == "powerbi://api.powerbi.com/v1.0/myorg/" + config["workspace_name"],
            "Wrong report workspace")


def body_from_folder(folder):
    parts = []
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.name != ".platform" and ".pbi" not in path.parts:
            parts.append({"path": path.relative_to(folder).as_posix(), "payloadType": "InlineBase64",
                          "payload": base64.b64encode(path.read_bytes()).decode()})
    return {"definition": {"parts": parts}}


def seal_release(folder, commit, build_id, branch):
    require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "Full commit SHA required")
    write_json(folder / "manifest.json", {"version": 1, "commit_sha": commit, "build_id": str(build_id),
        "source_branch": branch, "workspace_id": WORKSPACE, "gold_run_id": GOLD_RUN,
        "files": {p.relative_to(folder).as_posix(): digest(p) for p in sorted(folder.rglob("*"))
                  if p.is_file() and p != folder / "manifest.json" and "__pycache__" not in p.parts}})


def verify_release(folder, expected_commit=None, expected_build=None):
    manifest = read_json(folder / "manifest.json")
    require(manifest["version"] == 1 and manifest["workspace_id"] == WORKSPACE
            and manifest["gold_run_id"] == GOLD_RUN, "Wrong release target/version")
    if expected_commit is not None:
        require(manifest["commit_sha"] == expected_commit, "Release commit differs from selected CI run")
    if expected_build is not None:
        require(manifest["build_id"] == str(expected_build), "Release build differs from selected CI run")
    actual = {p.relative_to(folder).as_posix() for p in folder.rglob("*")
              if p.is_file() and p != folder / "manifest.json" and "__pycache__" not in p.parts}
    require(actual == set(manifest["files"]), "Release inventory differs")
    for name, checksum in manifest["files"].items():
        path = (folder / name).resolve()
        require(path.is_relative_to(folder.resolve()), "Release path escapes artifact")
        require(digest(path) == checksum, "Release checksum mismatch: " + name)
    config = read_json(folder / "config/environments/test.json")
    validate_definitions(read_json(folder / "model-update.json"), read_json(folder / "report-update.json"), config)
    return manifest, config


def build(project, output, commit, build_id, branch):
    require(not output.exists(), "Use a new release directory")
    config = read_json(project / "config/environments/test.json")
    validate_target(config)
    output.mkdir(parents=True)
    model_dir = output / "definitions/SM_EV_Analytics.SemanticModel"
    report_dir = output / "definitions/RPT_EV_Analytics.Report"
    for source, target in [(project / "SM_EV_Analytics.SemanticModel", model_dir),
                           (project / "RPT_EV_Analytics.Report", report_dir)]:
        shutil.copytree(source, target, ignore=shutil.ignore_patterns(".pbi", "__pycache__", "*.pyc"))
    expression = model_dir / "definition/expressions.tmdl"
    source_url = f"https://onelake.dfs.fabric.microsoft.com/{SOURCE_WORKSPACE}/{SOURCE_LAKEHOUSE}"
    text = expression.read_text(encoding="utf-8")
    require(text.count(source_url) == 1, "Expected one source lakehouse expression")
    expression.write_text(text.replace(source_url, f"https://onelake.dfs.fabric.microsoft.com/{WORKSPACE}/{TARGET_LAKEHOUSE}"), encoding="utf-8")
    database = model_dir / "definition/database.tmdl"
    database.write_text(re.sub(r"(?m)^\tid: " + SOURCE_MODEL + r"\s*\n", "", database.read_text(encoding="utf-8")), encoding="utf-8")
    for path in (model_dir / "definition/tables").glob("*.tmdl"):
        text = re.sub(r"(?m)^\t\t\tschemaName:.*\n", "", path.read_text(encoding="utf-8"))
        if config["lakehouse_schema"]:
            text = text.replace("\t\t\texpressionSource: GoldLakehouse", "\t\t\tschemaName: " + config["lakehouse_schema"] + "\n\t\t\texpressionSource: GoldLakehouse")
        path.write_text(text, encoding="utf-8")
    binding = read_json(report_dir / "definition.pbir")
    binding["datasetReference"] = {"byConnection": {"connectionString":
        f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{config['workspace_name']};"
        f"initial catalog={config['semantic_model_name']};access mode=readonly;"
        f"integrated security=ClaimsToken;semanticmodelid={TARGET_MODEL}"}}
    write_json(report_dir / "definition.pbir", binding)
    model, report = body_from_folder(model_dir), body_from_folder(report_dir)
    validate_definitions(model, report, config)
    write_json(output / "model-update.json", model)
    write_json(output / "report-update.json", report)
    (output / "config/environments").mkdir(parents=True)
    write_json(output / "config/environments/test.json", config)
    (output / "scripts").mkdir()
    for name in RUNTIME:
        shutil.copyfile(project / "scripts" / name, output / "scripts" / name)
    seal_release(output, commit, build_id, branch)
    verify_release(output, commit, build_id)
    print("Verified release:", output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--build-id", required=True)
    parser.add_argument("--branch", required=True)
    args = parser.parse_args()
    build(args.project, args.output, args.commit, args.build_id, args.branch)
