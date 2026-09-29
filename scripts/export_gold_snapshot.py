"""Export the pinned Gold v2 snapshot from downloaded Delta v0 active files.

Network transfer is performed by the authenticated Fabric OneLake connector.
This script plans exact downloads, validates source data, writes portable Parquet,
and verifies a completed export without requiring Fabric or Spark.
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
LOCAL_RUNTIME = PROJECT / ".tools" / "parquet-runtime"
if LOCAL_RUNTIME.exists():
    sys.path.insert(0, str(LOCAL_RUNTIME))

from star_schema import DIMENSIONS, dimension_key

GOLD_RUN = "20260925T152721965637Z"
WORKSPACE = "5fe78794-25c3-41ee-b35e-bc56542d2cea"
LAKEHOUSE = "32e99e91-38e9-4428-8fd2-6bcff6573088"
COUNTS = {"fact_ev_purchase_intent": 668665, "dim_demographics": 45,
          "dim_income": 4, "dim_mobility": 16, "dim_charging": 2,
          "dim_attitude_incentive": 30, "agg_ev_kpi": 1, "agg_ev_segments": 35}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_path(root, relative):
    require(not Path(relative).is_absolute(), "Absolute manifest path")
    result = (Path(root) / relative).resolve()
    require(result.is_relative_to(Path(root).resolve()), "Path escapes export directory")
    return result


def validate_audit(audit):
    require(audit["status"] == "verified" and audit["gold_schema_version"] == 2, "Gold v2 audit required")
    require(audit["gold_run_id"] == GOLD_RUN, "Unexpected Gold snapshot")
    for check in ("star_validation", "sql_validation"):
        require(audit[check]["status"] == "passed", f"Audit check failed: {check}")
    require(len(audit["tables"]) == 8, "Expected eight source tables")
    require({t["role"] for t in audit["tables"]} == set(COUNTS), "Incorrect table roles")
    for table in audit["tables"]:
        require(table["rows"] == COUNTS[table["role"]], "Unexpected audit row count")
        require(table["table"] == table["role"] + "_" + GOLD_RUN.lower(), "Mixed table snapshots")


def inspect_log(path, table):
    actions = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    protocols = [a["protocol"] for a in actions if "protocol" in a]
    metadata = [a["metaData"] for a in actions if "metaData" in a]
    require(len(protocols) == len(metadata) == 1, "Expected one v0 protocol and metadata action")
    protocol, meta = protocols[0], metadata[0]
    require(protocol["minReaderVersion"] == 1 and not protocol.get("readerFeatures"), "Unsupported Delta reader features")
    require(meta["format"]["provider"] == "parquet", "Source is not Parquet")
    require(not meta["partitionColumns"], "Partitioned snapshots require a Delta reader")
    require(meta["configuration"].get("delta.columnMapping.mode", "none") == "none", "Column mapping requires a Delta reader")
    require(not any("remove" in a for a in actions), "Unexpected v0 remove action")
    schema = json.loads(meta["schemaString"])
    aliases = {"long": "bigint", "integer": "int"}
    actual = [(f["name"], aliases.get(f["type"], f["type"])) for f in schema["fields"]]
    require(actual == [(c["name"], c["type"]) for c in table["columns"]], "Delta schema differs from verified audit")
    adds = [a["add"] for a in actions if "add" in a]
    require(bool(adds), "No active files in v0")
    require(len({a["path"] for a in adds}) == len(adds), "Duplicate add paths")
    for add in adds:
        require(not add.get("deletionVector") and not add.get("partitionValues"), "Unsupported logical file transformation")
        require(re.fullmatch(r"[A-Za-z0-9_.-]+\.parquet", add["path"]) is not None, "Unexpected Parquet file path")
    require(sum(json.loads(a["stats"])["numRecords"] for a in adds) == table["rows"], "Delta statistics row count mismatch")
    return meta, schema, sorted(adds, key=lambda a: a["path"])


def plan(staging, audit_path):
    audit = read_json(audit_path)
    validate_audit(audit)
    downloads = []
    for table in audit["tables"]:
        role = table["role"]
        _, _, adds = inspect_log(staging / "source_delta_logs" / (role + ".jsonl"), table)
        folder = staging / "source_parquet" / role
        folder.mkdir(parents=True, exist_ok=True)
        for add in adds:
            downloads.append({"role": role, "source": f"Tables/{table['table']}/{add['path']}",
                              "destination": str((folder / add["path"]).resolve()), "size": add["size"]})
    write_json(staging / "download_plan.json", downloads)
    return {"files": len(downloads), "bytes": sum(d["size"] for d in downloads)}


def arrow_schema(delta_schema):
    import pyarrow as pa
    simple = {"string": pa.string(), "long": pa.int64(), "integer": pa.int32(),
              "double": pa.float64(), "timestamp": pa.timestamp("us", tz="UTC")}
    fields = []
    for field in delta_schema["fields"]:
        datatype = field["type"]
        if datatype.startswith("decimal("):
            precision, scale = map(int, datatype[8:-1].split(","))
            arrow_type = pa.decimal128(precision, scale)
        else:
            arrow_type = simple[datatype]
        fields.append(pa.field(field["name"], arrow_type, nullable=field["nullable"]))
    return pa.schema(fields)


def validate_tables(tables, audit, expected, spec):
    frames = {role: table.to_pandas() for role, table in tables.items()}
    for role, frame in frames.items():
        require(len(frame) == COUNTS[role], f"Row mismatch: {role}")
        for key in ("gold_run_id", "silver_run_id"):
            require(frame[key].notna().all() and frame[key].eq(audit[key]).all(), f"Mixed lineage: {role}/{key}")
    fact = frames["fact_ev_purchase_intent"]
    for key in ("id", "record_key"):
        require(fact[key].notna().all() and fact[key].is_unique, f"Invalid fact key: {key}")
    require(fact["Will_Buy_EV"].isin(["Yes", "No"]).all(), "Invalid target label")
    require(fact["will_buy_ev_flag"].eq(fact["Will_Buy_EV"].eq("Yes").astype(int)).all(), "Target flag mismatch")
    require(fact["source_sha256"].str.upper().eq(expected["source_sha256"].upper()).all(), "Source dataset checksum mismatch")
    kpi = {"respondent_count": len(fact), "yes_count": int(fact["will_buy_ev_flag"].sum())}
    kpi["no_count"] = kpi["respondent_count"] - kpi["yes_count"]
    kpi["purchase_intent_rate"] = kpi["yes_count"] / kpi["respondent_count"]
    audit_kpi = frames["agg_ev_kpi"].iloc[0]
    for key, value in kpi.items():
        require(abs(value - expected[key]) < 1e-12, f"Reference KPI mismatch: {key}")
        require(abs(value - audit_kpi[key]) < 1e-12, f"Audit KPI mismatch: {key}")
    enriched = fact
    for dim in DIMENSIONS:
        role, key, attrs = dim["role"], dim["key"], dim["attributes"]
        frame = frames[role]
        require(frame[key].notna().all() and frame[key].is_unique, f"Invalid dimension PK: {role}")
        require(not frame[attrs].isna().any().any() and not frame.duplicated(attrs).any(), f"Invalid dimension attributes: {role}")
        for row in frame.to_dict("records"):
            require(row[key] == dimension_key(role, [row[a] for a in attrs]), f"Dimension hash mismatch: {role}")
            for attr in attrs:
                if attr in spec["bands"]:
                    require(row[attr + "_sort"] == spec["bands"][attr]["labels"].index(row[attr]) + 1, "Band sort mismatch")
        require(fact[key].notna().all() and fact[key].isin(frame[key]).all(), f"Orphan FK: {key}")
        enriched = enriched.merge(frame[[key, *attrs]], on=key, validate="many_to_one", how="left")
    segment_audit = frames["agg_ev_segments"]
    segment_keys = ["segment_dimension", "segment_value"]
    require(not segment_audit[segment_keys].isna().any().any() and not segment_audit.duplicated(segment_keys).any(), "Invalid segment audit key")
    expected_groups = {(r["segment_dimension"], r["segment_value"]): r for r in expected["segments"]}
    actual_groups = {(r["segment_dimension"], r["segment_value"]): r for r in segment_audit.to_dict("records")}
    require(set(actual_groups) == set(expected_groups), "Segment group mismatch")
    for (column, value), reference in expected_groups.items():
        subset = enriched.loc[enriched[column] == value]
        n, yes = len(subset), int(subset["will_buy_ev_flag"].sum())
        actual = actual_groups[column, value]
        require((n, yes) == (reference["respondent_count"], reference["yes_count"]), "Fact segment mismatch")
        require((n, yes, n - yes) == (actual["respondent_count"], actual["yes_count"], actual["no_count"]), "Aggregate segment mismatch")
        require(abs(actual["purchase_intent_rate"] - yes / n) < 1e-12, "Segment rate mismatch")
    return {"status": "passed", "kpi": kpi, "orphan_keys": 0,
            "primary_keys": "passed", "dimension_hashes_and_sort": "passed",
            "lineage": "passed", "segment_groups": len(actual_groups)}


def build(staging, audit_path, output):
    import pyarrow as pa
    import pyarrow.parquet as pq
    audit = read_json(audit_path)
    validate_audit(audit)
    output.mkdir(parents=True, exist_ok=False)
    (output / "parquet").mkdir()
    evidence = output / "evidence"
    evidence.mkdir()
    copies = {"source_audit.json": audit_path,
              "gold_expected_metrics.json": PROJECT / "metadata/gold_expected_metrics.json",
              "gold_spec.json": PROJECT / "metadata/gold_spec.json"}
    for name, source in copies.items():
        shutil.copyfile(source, evidence / name)
    shutil.copytree(staging / "source_delta_logs", evidence / "source_delta_logs")
    for name in ("download_receipts.json", "log_download_receipts.json"):
        require((staging / name).is_file(), f"Missing transfer evidence: {name}")
        shutil.copyfile(staging / name, evidence / name)
    receipts = {r["source"]: r for r in read_json(staging / "download_receipts.json")}
    tables, entries = {}, []
    for table in audit["tables"]:
        role = table["role"]
        meta, schema, adds = inspect_log(staging / "source_delta_logs" / (role + ".jsonl"), table)
        chunks, source_files = [], []
        target_schema = arrow_schema(schema)
        for add in adds:
            path = staging / "source_parquet" / role / add["path"]
            require(path.stat().st_size == add["size"], f"Incomplete download: {path.name}")
            source_path = f"Tables/{table['table']}/{add['path']}"
            receipt = receipts[source_path]
            require(receipt["contentLength"] == add["size"] and bool(receipt["etag"]), "Transfer metadata mismatch")
            data = pq.read_table(path, coerce_int96_timestamp_unit="us")
            require(data.column_names == target_schema.names, "Physical column mapping mismatch")
            for field, target_field in zip(data.schema, target_schema):
                valid = field.type == target_field.type or (pa.types.is_timestamp(field.type) and pa.types.is_timestamp(target_field.type))
                require(valid, f"Physical type mismatch: {role}/{field.name}")
            data = data.cast(target_schema, safe=True)
            require(data.num_rows == json.loads(add["stats"])["numRecords"], "Source file rows differ from Delta log")
            chunks.append(data)
            source_files.append({"path": source_path, "bytes": add["size"], "sha256": sha256(path),
                                 "etag": receipt["etag"], "rows": data.num_rows})
        source = pa.concat_tables(chunks).combine_chunks()
        destination = output / "parquet" / (role + ".parquet")
        pq.write_table(source, destination, compression="snappy", version="2.6")
        readback = pq.read_table(destination)
        require(source.equals(readback, check_metadata=False), f"Export readback differs: {role}")
        tables[role] = readback
        entries.append({"role": role, "source_table": table["table"], "restore_table": table["table"],
                        "source_delta_version": 0, "source_delta_table_id": meta["id"],
                        "path": destination.relative_to(output).as_posix(), "rows": readback.num_rows,
                        "bytes": destination.stat().st_size, "sha256": sha256(destination),
                        "schema": schema, "arrow_schema": str(readback.schema),
                        "source_files": source_files, "readback_exact_equality": True})
        print(f"Exported {role}: {readback.num_rows} rows", flush=True)
    validation = validate_tables(tables, audit, read_json(evidence / "gold_expected_metrics.json"), read_json(evidence / "gold_spec.json"))
    relationships = [{"from_table": "fact_ev_purchase_intent", "from_column": d["key"],
                      "to_table": d["role"], "to_column": d["key"], "cardinality": "many_to_one",
                      "filter_direction": "dimension_to_fact", "active": True} for d in DIMENSIONS]
    primary_keys = {"fact_ev_purchase_intent": ["id"], "agg_ev_segments": ["segment_dimension", "segment_value"]}
    primary_keys.update({d["role"]: [d["key"]] for d in DIMENSIONS})
    manifest = {"manifest_version": 1, "status": "export_verified", "gold_schema_version": 2,
                "export_id": output.name, "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "gold_run_id": GOLD_RUN, "silver_run_id": audit["silver_run_id"],
                "pipeline_run_id": audit["pipeline_run_id"], "source_workspace_id": WORKSPACE,
                "source_lakehouse_id": LAKEHOUSE, "source_delta_version": 0,
                "method": "OneLake downloads of exact Delta v0 add files; PyArrow Parquet reserialization",
                "source_guardrails": {"reader_version": 1, "partitioned": False, "column_mapping": False, "deletion_vectors": False},
                "pipeline_rerun": False, "timestamp_timezone": "UTC", "timestamp_unit": "microseconds",
                "checksum_algorithm": "SHA-256", "parquet_compression": "snappy", "pyarrow_version": pa.__version__,
                "tables": entries, "primary_keys": primary_keys, "single_row_tables": ["agg_ev_kpi"],
                "relationships": relationships, "validation": validation,
                "isolated_recovery_test": "not_started", "remaining_dashboard_checks": "skipped_by_user_request",
                "evidence_files": [{"path": p.relative_to(output).as_posix(), "bytes": p.stat().st_size, "sha256": sha256(p)}
                                   for p in sorted(evidence.rglob("*")) if p.is_file()]}
    write_json(output / "manifest.json", manifest)
    (output / "manifest.sha256").write_text(sha256(output / "manifest.json") + "  manifest.json\n", encoding="ascii")
    return verify(output)


def verify(root):
    require(sha256(root / "manifest.json") == (root / "manifest.sha256").read_text().split()[0], "Manifest checksum mismatch")
    import pyarrow.parquet as pq
    manifest = read_json(root / "manifest.json")
    require(manifest["status"] == "export_verified" and manifest["gold_run_id"] == GOLD_RUN, "Invalid manifest status/snapshot")
    require(len(manifest["tables"]) == 8 and {t["role"] for t in manifest["tables"]} == set(COUNTS), "Missing or duplicate tables")
    for entry in manifest["tables"] + manifest["evidence_files"]:
        path = safe_path(root, entry["path"])
        require(path.stat().st_size == entry["bytes"] and sha256(path) == entry["sha256"], f"File checksum mismatch: {entry['path']}")
    expected_paths = {safe_path(root, t["path"]) for t in manifest["tables"]}
    require({p.resolve() for p in (root / "parquet").rglob("*.parquet")} == expected_paths, "Unexpected Parquet file set")
    tables = {}
    for entry in manifest["tables"]:
        table = pq.read_table(safe_path(root, entry["path"]))
        require(table.schema.equals(arrow_schema(entry["schema"]), check_metadata=False), "Parquet schema mismatch")
        require(table.num_rows == entry["rows"] == COUNTS[entry["role"]], "Parquet row mismatch")
        tables[entry["role"]] = table
    audit = read_json(root / "evidence/source_audit.json")
    validate_audit(audit)
    result = validate_tables(tables, audit, read_json(root / "evidence/gold_expected_metrics.json"), read_json(root / "evidence/gold_spec.json"))
    result.update({"export_directory": str(root.resolve()), "manifest_sha256": sha256(root / "manifest.json"),
                   "tables": len(tables), "parquet_files": len(tables), "parquet_bytes": sum(t["bytes"] for t in manifest["tables"])})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "build", "verify"])
    parser.add_argument("--staging", type=Path, default=PROJECT / "output/gold_export_staging")
    parser.add_argument("--audit", type=Path, default=PROJECT / "metadata/e2e_star_verified_run.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "plan":
        result = plan(args.staging, args.audit)
    else:
        require(args.output is not None, "--output is required")
        result = build(args.staging, args.audit, args.output) if args.command == "build" else verify(args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
