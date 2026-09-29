"""Shared, dependency-free checks for the pinned recovery package."""
import hashlib
import json
import re
from pathlib import Path
from uuid import UUID

GOLD_RUN = "20260925T152721965637Z"
MANIFEST_SHA256 = "0da1b98e56c024261d247e3cfe94efaddb594cd52cce4eee89f6a8955cf1ad9f"
SOURCE_WORKSPACE = "5fe78794-25c3-41ee-b35e-bc56542d2cea"
SOURCE_LAKEHOUSE = "32e99e91-38e9-4428-8fd2-6bcff6573088"
SOURCE_MODEL = "8e7e37b7-7bab-4122-84fb-3ae7b2121cd7"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_path(root, relative):
    require(not Path(relative).is_absolute(), "Absolute relative path")
    path = (Path(root) / relative).resolve()
    require(path.is_relative_to(Path(root).resolve()), "Path escapes root")
    return path


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value), "Use letters, digits and underscores for recovery names")
    return value


def validate_config(config, report=False):
    require(config.get("config_version") == 1, "Unsupported recovery config")
    require(config.get("gold_run_id") == GOLD_RUN, "Wrong Gold run")
    require(config.get("snapshot_manifest_sha256") == MANIFEST_SHA256, "Wrong snapshot checksum")
    for key in ("workspace_id", "lakehouse_id") + (("semantic_model_id",) if report else ()):
        value = config.get(key)
        require(isinstance(value, str), f"Fill in {key} with the NEW item ID")
        require(str(UUID(value)) == value.lower(), f"Invalid UUID: {key}")
        require(UUID(value).int != 0, f"Placeholder UUID: {key}")
    require(config["workspace_id"].lower() != SOURCE_WORKSPACE, "Recovery must use a separate workspace")
    require(config["lakehouse_id"].lower() != SOURCE_LAKEHOUSE, "Cannot target the source lakehouse")
    if config.get("semantic_model_id"):
        require(config["semantic_model_id"].lower() != SOURCE_MODEL, "Cannot target the source semantic model")
    for key in ("workspace_name", "lakehouse_name", "semantic_model_name", "report_name"):
        identifier(config[key])
    schema = config.get("lakehouse_schema")
    require(isinstance(schema, str), "lakehouse_schema must be a string (empty for legacy lakehouses)")
    if schema:
        identifier(schema)
    require(config.get("snapshot_relative_path") == "Files/recovery/snapshot", "Keep the documented snapshot upload path")
    return config


def validate_context(context, config):
    validate_config(config)
    expected = {"currentWorkspaceId": config["workspace_id"],
                "defaultLakehouseWorkspaceId": config["workspace_id"],
                "defaultLakehouseId": config["lakehouse_id"]}
    for key, value in expected.items():
        require(str(context.get(key, "")).lower() == value.lower(), f"Wrong or missing notebook context: {key}")


def check_snapshot(root):
    root = Path(root)
    require(sha256(root / "manifest.json") == MANIFEST_SHA256, "Snapshot manifest does not match the verified export")
    require((root / "manifest.sha256").read_text().split()[0] == MANIFEST_SHA256, "Manifest checksum sidecar mismatch")
    manifest = read_json(root / "manifest.json")
    require(manifest["gold_run_id"] == GOLD_RUN and manifest["status"] == "export_verified", "Snapshot is not verified")
    expected = set()
    for entry in manifest["tables"] + manifest["evidence_files"]:
        path = safe_path(root, entry["path"])
        require(path.stat().st_size == entry["bytes"] and sha256(path) == entry["sha256"], f"File integrity failure: {entry['path']}")
        expected.add(path)
    actual = {p.resolve() for p in root.rglob("*") if p.is_file()}
    require(actual == expected | {(root / "manifest.json").resolve(), (root / "manifest.sha256").resolve()}, "Unexpected or missing snapshot files")
    return manifest
