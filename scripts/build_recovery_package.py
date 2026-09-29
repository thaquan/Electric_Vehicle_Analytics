"""Build an allowlisted, self-contained project release with the verified snapshot."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import zipfile

from recovery_common import check_snapshot, read_json, require, sha256, write_json
from verify_recovery_package import verify

PROJECT = Path(__file__).resolve().parents[1]
FOLDERS = ["scripts", "notebooks", "sql", "tests", "models", "config", "docs", "metadata",
           "SM_EV_Analytics.SemanticModel", "RPT_EV_Analytics.Report", "NB_EV_Bronze_To_Silver.Notebook",
           "NB_EV_Silver_To_Gold.Notebook", "LH_EV_Bronze.Lakehouse", "LH_EV_Silver.Lakehouse",
           "LH_EV_Gold.Lakehouse", "PL_EV_E2E.DataPipeline"]
FILES = ["README.md", "RPT_EV_Analytics.pbip", "requirements.txt", "requirements-export.txt"]
EXCLUDED_PARTS = {".git", ".pbi", ".tools", ".venv", "__pycache__", "output", "node_modules"}
EXCLUDED_FILES = {"localSettings.json", "report_create_payload.json", "star_model_binding_request.json",
                  "gold_recovery_package_status.json", "recovery_model_get_definition.json",
                  "recovery_model_live_definition.json"}


def include(path):
    return not (set(path.parts) & EXCLUDED_PARTS) and path.name not in EXCLUDED_FILES and path.suffix != ".pyc"


def build(snapshot, destination):
    manifest = check_snapshot(snapshot)
    require(not destination.exists(), "Choose a new release directory")
    destination.mkdir(parents=True)
    root = destination / "EV_Analytics_Recovery"
    root.mkdir()
    shutil.copytree(snapshot, root / "snapshot")
    for folder in FOLDERS:
        for file in sorted((PROJECT / folder).rglob("*")):
            relative = file.relative_to(PROJECT)
            if not file.is_file() or not include(relative):
                continue
            require(not file.is_symlink(), "Do not bundle links")
            target = root / "project" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if file.suffix == ".ipynb":
                notebook = read_json(file)
                for cell in notebook["cells"]:
                    if cell["cell_type"] == "code":
                        cell["outputs"] = []
                        cell["execution_count"] = None
                notebook.get("metadata", {}).pop("widgets", None)
                write_json(target, notebook)
            else:
                shutil.copyfile(file, target)
    for name in FILES:
        shutil.copyfile(PROJECT / name, root / "project" / name)
    shutil.copyfile(PROJECT / "docs/recovery_quickstart.md", root / "README.md")
    shutil.copyfile(PROJECT / "config/recovery.example.json", root / "recovery.example.json")
    shutil.copyfile(PROJECT / "scripts/verify_recovery_package.py", root / "verify_package.py")
    export_status = read_json(root / "project/metadata/gold_export_status.json")
    export_status["local_directory"] = "../snapshot"
    export_status["parts"].update({"3_project_packaging": "completed", "4_recovery_procedure": "completed"})
    export_status["package_note"] = "Snapshot path is relative to project/. Original OneLake identifiers are provenance."
    write_json(root / "project/metadata/gold_export_status.json", export_status)
    write_json(root / "project/metadata/gold_recovery_package_status.json", {
        "part_3_packaging": "completed", "part_4_recovery_procedure": "completed", "part_5_isolated_recovery": "not_started",
        "package_inventory": "../../package_manifest.json", "release_information": "../../release.json",
        "zip_checksum": "Use the .zip.sha256 sidecar delivered with the ZIP",
        "remaining_dashboard_checks": "skipped_by_user_request"})
    stamp = datetime.now(timezone.utc).isoformat()
    write_json(root / "release.json", {"created_at_utc": stamp, "gold_run_id": manifest["gold_run_id"],
               "export_id": manifest["export_id"], "packaging": "completed", "recovery_runbook": "prepared",
               "isolated_recovery": "not_started", "remaining_dashboard_checks": "skipped_by_user_request",
               "historical_source_artifacts": "project/ contains the source project; prepare_recovery.py creates new target bindings",
               "toolchain": {"python": "3.11+ (tested with 3.13)", "pyarrow": "25.0.1", "report_authoring_cli": "0.4.0"}})
    inventory = {"package_version": 1, "created_at_utc": stamp, "gold_run_id": manifest["gold_run_id"],
                 "snapshot_manifest_sha256": sha256(snapshot / "manifest.json"), "files": [
                     {"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)}
                     for p in sorted(root.rglob("*")) if p.is_file()]}
    write_json(root / "package_manifest.json", inventory)
    (root / "package_manifest.sha256").write_text(sha256(root / "package_manifest.json") + "  package_manifest.json\n", encoding="ascii")
    directory_result = verify(root)
    archive_path = destination / ("EV_Analytics_Recovery_" + manifest["gold_run_id"] + ".zip")
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for file in sorted(root.rglob("*")):
            if file.is_file():
                archive.write(file, "EV_Analytics_Recovery/" + file.relative_to(root).as_posix())
    archive_hash = sha256(archive_path)
    archive_path.with_suffix(".zip.sha256").write_text(archive_hash + "  " + archive_path.name + "\n", encoding="ascii")
    zip_result = verify(archive_path)
    result = {"status": "package_verified", "created_at_utc": stamp, "zip": str(archive_path.resolve()),
              "directory": str(root.resolve()), "bytes": archive_path.stat().st_size, "sha256": archive_hash,
              "directory_verification": directory_result, "zip_verification": zip_result,
              "part_3_packaging": "completed", "part_4_recovery_procedure": "completed",
              "part_5_isolated_recovery": "not_started", "pipeline_rerun": False}
    write_json(destination / "package_verification.json", result)
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot", type=Path, required=True)
    p.add_argument("--destination", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(build(a.snapshot, a.destination), indent=2))
