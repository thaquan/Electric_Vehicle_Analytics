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
