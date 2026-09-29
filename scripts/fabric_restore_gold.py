"""Run only inside a fresh Fabric notebook attached to the NEW lakehouse."""
from datetime import datetime, timezone
from pathlib import Path

from recovery_common import (check_snapshot, require,
                             validate_config, validate_context, write_json)


def restore(spark, context, config, execute=False):
    validate_config(config)
    validate_context(context, config)
    root = Path("/lakehouse/default") / config["snapshot_relative_path"]
    manifest = check_snapshot(root)
    # Reuse the independently verified PyArrow/pandas checks on the copied input.
    from export_gold_snapshot import verify
    source_check = verify(root)
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    spark.conf.set("spark.sql.timestampType", "TIMESTAMP_LTZ")
    schema = config["lakehouse_schema"]
    prefix = schema + "." if schema else ""
    targets = {t["role"]: prefix + t["restore_table"] for t in manifest["tables"]}
    collisions = [name for name in targets.values() if spark.catalog.tableExists(name)]
    require(not collisions, "Destination tables already exist; no writes made: " + ", ".join(collisions))
    uri = f"abfss://{config['workspace_id']}@onelake.dfs.fabric.microsoft.com/{config['lakehouse_id']}"
    aliases = {"long": "bigint", "integer": "int"}
    frames = {}
    # Read and validate every Parquet table before the first write.
    for table in manifest["tables"]:
        df = spark.read.parquet(uri + "/" + config["snapshot_relative_path"] + "/" + table["path"])
        expected = [(f["name"], aliases.get(f["type"], f["type"])) for f in table["schema"]["fields"]]
        require(df.dtypes == expected, "Spark schema mismatch: " + table["role"])
        require(df.count() == table["rows"], "Spark row mismatch: " + table["role"])
        frames[table["role"]] = df
    if not execute:
        return {"status": "preflight_passed_no_tables_written", "target_workspace_id": config["workspace_id"],
                "target_lakehouse_id": config["lakehouse_id"], "tables": targets, "source_validation": source_check}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    result_path = Path("/lakehouse/default/Files/recovery/results") / ("restore_data_" + stamp + ".json")
    result_path.parent.mkdir(parents=True, exist_ok=True)
    evidence = {"status": "in_progress", "recovery_run_id": stamp, "gold_run_id": manifest["gold_run_id"],
                "manifest_sha256": config["snapshot_manifest_sha256"], "workspace_id": config["workspace_id"],
                "lakehouse_id": config["lakehouse_id"], "written_tables": [], "verified_tables": [],
                "source_validation": source_check, "semantic_model_refresh": "not_started",
                "report_publish": "not_started", "isolated_recovery_complete": False,
                "remaining_dashboard_checks": "skipped_by_user_request"}
    write_json(result_path, evidence)
    try:
        for table in manifest["tables"]:
            role = table["role"]
            df = frames[role]
            location = uri + "/Tables/" + (schema + "/" if schema else "") + table["restore_table"]
            df.write.format("delta").mode("errorifexists").option("path", location).saveAsTable(targets[role])
            evidence["written_tables"].append(targets[role])
            write_json(result_path, evidence)
            # Read through the registered table, as the semantic model will.
            restored = spark.table(targets[role]).select(*df.columns)
            require(restored.dtypes == df.dtypes and restored.count() == table["rows"], "Restored table schema/count mismatch")
            require(df.exceptAll(restored).limit(1).count() == 0 and restored.exceptAll(df).limit(1).count() == 0,
                    "Restored Delta data differs from Parquet: " + role)
            evidence["verified_tables"].append({"table": targets[role], "rows": table["rows"], "exact_multiset_equality": True})
            write_json(result_path, evidence)
        evidence["status"] = "data_restored_and_verified"
        evidence["kpi"] = source_check["kpi"]
        evidence["orphan_keys"] = source_check["orphan_keys"]
        evidence["segment_groups"] = source_check["segment_groups"]
        evidence["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    except Exception as error:
        evidence["status"] = "failed_partial_restore"
        evidence["error"] = str(error)
        raise
    finally:
        write_json(result_path, evidence)
    print("Recovery data evidence:", str(result_path))
    return evidence
