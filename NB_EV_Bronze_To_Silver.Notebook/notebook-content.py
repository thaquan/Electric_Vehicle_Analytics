# Fabric notebook source

# METADATA ********************
# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "676ba346-22dd-4eeb-92ec-4f53f09ccca7",
# META       "default_lakehouse_name": "LH_EV_Silver",
# META       "default_lakehouse_workspace_id": "5fe78794-25c3-41ee-b35e-bc56542d2cea",
# META       "known_lakehouses": [
# META         {
# META           "id": "676ba346-22dd-4eeb-92ec-4f53f09ccca7"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

# MAGIC %%configure -f
# MAGIC {
# MAGIC   "defaultLakehouse": {
# MAGIC     "name": "LH_EV_Silver",
# MAGIC     "id": "676ba346-22dd-4eeb-92ec-4f53f09ccca7",
# MAGIC     "workspaceId": "5fe78794-25c3-41ee-b35e-bc56542d2cea"
# MAGIC   }
# MAGIC }

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# PARAMETERS CELL ********************

pipeline_run_id = ""
run_mode = "publish"


# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import json
import notebookutils
"""Pure validation of pipeline arguments and immutable publication markers."""
import re


def check_run_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{8}T\d{12}Z", value):
        raise ValueError("A valid publication run ID is required")
    return value


def check_pipeline_id(value, required=False):
    if required and not value:
        raise ValueError("Pipeline run ID was not injected; check the notebook parameter cell")
    if value and not re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", value):
        raise ValueError("Invalid pipeline run ID")


def require_publication(marker, stage, run_id, pipeline_run_id="", silver_run_id=None):
    check_run_id(run_id)
    if marker.get("status") != "published" or marker.get("run_id") != run_id:
        raise ValueError("Missing or mismatched publication marker")
    if pipeline_run_id and marker.get("pipeline_run_id") != pipeline_run_id:
        raise ValueError("Publication belongs to another pipeline execution")
    suffix = run_id.lower()
    if stage == "silver":
        expected = {f"silver_train_{suffix}": 668665, f"silver_test_{suffix}": 286571, f"silver_original_reference_{suffix}": 10000}
    elif stage == "gold":
        expected = {f"fact_ev_purchase_intent_{suffix}": 668665, f"agg_ev_kpi_{suffix}": 1, f"agg_ev_segments_{suffix}": 35}
        if marker.get("silver_run_id") != silver_run_id:
            raise ValueError("Gold does not reference the selected Silver run")
        if marker.get("respondent_count") != 668665 or marker.get("yes_count") != 116779:
            raise ValueError("Gold KPI marker mismatch")
    else:
        raise ValueError("Unsupported publication stage")
    tables = marker.get("tables", [])
    if len(tables) != len(expected) or {t.get("table"): t.get("rows") for t in tables} != expected:
        raise ValueError("Publication table set/count mismatch")
    return expected


# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

def execute_silver():
    """Run NB_EV_Bronze_To_Silver with LH_EV_Silver as the default Lakehouse."""
    import json
    import sys
    import tempfile
    from datetime import datetime, timezone
    from pathlib import Path

    from pyspark.sql import functions as F
    from pyspark.sql import SparkSession
    import notebookutils

    check_pipeline_id(pipeline_run_id, required=bool(notebookutils.runtime.context.get("isForPipeline")))
    if run_mode not in ("publish", "validate_only"):
        raise ValueError("Unsupported Silver run mode")
    context = notebookutils.runtime.context
    if context.get("defaultLakehouseId") != "676ba346-22dd-4eeb-92ec-4f53f09ccca7" or context.get("defaultLakehouseWorkspaceId") != "5fe78794-25c3-41ee-b35e-bc56542d2cea":
        raise RuntimeError(f"Expected LH_EV_Silver in WS_EV_Analytics; actual Lakehouse={context.get('defaultLakehouseId')!r}, workspace={context.get('defaultLakehouseWorkspaceId')!r}. Sync the latest notebook and start a fresh pipeline run so its first %%configure cell is applied.")
    BASE = Path("/lakehouse/default/Files")
    WORKSPACE_ID = "5fe78794-25c3-41ee-b35e-bc56542d2cea"
    BRONZE_ID = "c1516bc3-3ae5-4a7f-966e-16a6c8126ec5"
    BRONZE_URI = f"abfss://{WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{BRONZE_ID}/Files"
    sys.path.insert(0, str(BASE / "code"))
    from bronze_silver import INTEGERS, DECIMALS, SOURCES, prepare, read_json

    spark = SparkSession.builder.getOrCreate()
    # Hard fail on invalid casts instead of silently introducing nulls.
    spark.conf.set("spark.sql.ansi.enabled", "true")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    report_path = BASE / f"quality/{run_id}.json"
    # This snapshot is small (~65 MB CSV); driver-side validation is intentional.
    # All inputs pass before any Silver table is created.
    with tempfile.TemporaryDirectory(prefix="ev_bronze_") as local:
        local = Path(local)
        (local / "metadata").mkdir()
        (local / "raw").mkdir()
        for filename in ("source_manifest.json", "categorical_profile.json", "profiling_summary.json"):
            notebookutils.fs.cp(f"{BRONZE_URI}/metadata/{filename}", (local / "metadata" / filename).as_uri())
        manifest = read_json(local / "metadata/source_manifest.json")
        for entry in manifest["files"]:
            notebookutils.fs.cp(f"{BRONZE_URI}/bronze/kaggle/{entry['name']}", (local / "raw" / entry["name"]).as_uri())
        validated = prepare(local / "raw", local / "metadata", report_path)
        del validated
    if run_mode == "validate_only":
        return {"status": "validated", "stage": "bronze", "pipeline_run_id": pipeline_run_id, "quality_run_id": run_id}
    staged = []
    for source, filename in SOURCES.items():
        entry = next(e for e in manifest["files"] if e["name"] == filename)
        frame = spark.read.option("header", True).option("inferSchema", False).option("mode", "FAILFAST").csv(f"{BRONZE_URI}/bronze/kaggle/{filename}")
        for column in frame.columns:
            if column in INTEGERS:
                frame = frame.withColumn(column, F.col(column).cast("long" if column == "id" else "int"))
            elif column in DECIMALS:
                frame = frame.withColumn(column, F.col(column).cast("decimal(18,4)"))
        if "Will_Buy_EV" in frame.columns:
            frame = frame.withColumn("will_buy_ev_flag", F.when(F.col("Will_Buy_EV") == "Yes", 1).otherwise(0))
        key = "Buyer_ID" if source == "original_reference" else "id"
        frame = (frame.withColumn("source_dataset", F.lit(source))
                 .withColumn("source_file", F.lit(filename))
                 .withColumn("source_sha256", F.lit(entry["sha256"]))
                 .withColumn("processed_at_utc", F.lit(read_json(report_path)["checked_at_utc"]).cast("timestamp"))
                 .withColumn("record_key", F.concat(F.lit(source + ":"), F.col(key).cast("string"))))
        # Versioned tables avoid overwriting a previously successful run.
        table = f"silver_{source}_{run_id.lower()}"
        staged.append((table, frame, entry["data_rows"]))

    published = []
    for table, frame, expected in staged:
        frame.write.format("delta").mode("errorifexists").saveAsTable(table)
        actual = spark.table(table).count()
        if actual != expected:
            raise ValueError(f"{table}: written count {actual} != {expected}")
        published.append({"table": table, "rows": actual})
    # Consumers only use a run with this final success marker. Delta commits are per table.
    success = BASE / f"quality/{run_id}_published.json"
    result = {"status": "published", "run_id": run_id, "pipeline_run_id": pipeline_run_id, "tables": published}
    success.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result

result = execute_silver()
print(json.dumps(result, indent=2))


# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

if notebookutils.runtime.context.get("isForPipeline") or notebookutils.runtime.context.get("isReferenceRun"):
    notebookutils.notebook.exit(json.dumps(result))


# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
