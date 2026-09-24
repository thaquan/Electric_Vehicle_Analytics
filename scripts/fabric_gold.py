def execute_gold(input_gold_run_id):
    """Notebook body; CONFIG, SPEC, EXPECTED and band rules are embedded by the builder."""
    import json
    from datetime import datetime, timezone
    from functools import reduce
    from pathlib import Path

    import notebookutils
    from pyspark.sql import SparkSession, functions as F

    check_pipeline_id(pipeline_run_id, required=bool(notebookutils.runtime.context.get("isForPipeline")))
    require_gold_context(notebookutils.runtime.context, CONFIG)
    if run_mode not in ("publish", "verify_silver", "verify_gold"):
        raise ValueError("Unsupported Gold run mode")
    if notebookutils.runtime.context.get("isForPipeline") and not silver_run_id:
        raise ValueError("Pipeline must supply the Silver run produced by Build_Silver")
    SPEC = dict(DEFAULT_SPEC)
    SPEC["silver_run_id"] = check_run_id(silver_run_id or SPEC["silver_run_id"])
    SPEC["source_table"] = "silver_train_" + SPEC["silver_run_id"].lower()
    SPEC["source_relative_path"] = "Tables/" + SPEC["source_table"]

    spark = SparkSession.builder.getOrCreate()
    spark.conf.set("spark.sql.ansi.enabled", "true")
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    silver_uri = f"abfss://{CONFIG['workspace_id']}@onelake.dfs.fabric.microsoft.com/{CONFIG['silver_lakehouse_id']}"
    published = json.loads(notebookutils.fs.head(f"{silver_uri}/Files/quality/{SPEC['silver_run_id']}_published.json", 65536))
    require_publication(published, "silver", SPEC["silver_run_id"], pipeline_run_id)
    if run_mode == "verify_silver":
        verify_published_tables(spark, silver_uri, published, "silver", EXPECTED)
        return {"status": "verified", "stage": "silver", "run_id": SPEC["silver_run_id"], "pipeline_run_id": pipeline_run_id}
    if run_mode == "verify_gold":
        check_run_id(input_gold_run_id)
        gold_uri = f"abfss://{CONFIG['workspace_id']}@onelake.dfs.fabric.microsoft.com/{CONFIG['gold_lakehouse_id']}"
        gold_marker = json.loads(notebookutils.fs.head(f"{gold_uri}/Files/quality/{input_gold_run_id}_published.json", 65536))
        require_publication(gold_marker, "gold", input_gold_run_id, pipeline_run_id, SPEC["silver_run_id"])
        verify_published_tables(spark, gold_uri, gold_marker, "gold", EXPECTED)
        result = {"status": "verified", "stage": "e2e", "pipeline_run_id": pipeline_run_id, "silver_run_id": SPEC["silver_run_id"], "gold_run_id": input_gold_run_id, "tables": gold_marker["tables"]}
        if pipeline_run_id:
            audit = Path(f"/lakehouse/default/Files/pipeline_runs/{pipeline_run_id}.json")
            audit.parent.mkdir(parents=True, exist_ok=True)
            audit.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    source_entry = next(t for t in published["tables"] if t["table"] == SPEC["source_table"])
    if source_entry["rows"] != EXPECTED["respondent_count"]:
        raise ValueError("Silver publication row count mismatch")

    # Compare Spark CASE expressions with explicit threshold fixtures before touching Gold.
    for band in SPEC["bands"].values():
        points = [(None, "Unknown")]
        for index, edge in enumerate(band["edges"]):
            points.extend([(float(edge) - 0.01, band["labels"][index]), (float(edge), band["labels"][index + 1])])
        fixture = spark.createDataFrame(points, f"{band['column']} double, expected string")
        if fixture.selectExpr("expected", band_sql(band) + " AS actual").where("expected <> actual").count():
            raise ValueError(f"Band boundary test failed: {band['column']}")

    source_path = f"{silver_uri}/{SPEC['source_relative_path']}"
    source = spark.read.format("delta").option("versionAsOf", 0).load(source_path).cache()
    source_stats = source.agg(F.count("*").alias("rows"), F.countDistinct("id").alias("keys"), F.sum("will_buy_ev_flag").alias("yes")).first()
    if (source_stats.rows, source_stats.keys, source_stats.yes) != (EXPECTED["respondent_count"], EXPECTED["respondent_count"], EXPECTED["yes_count"]):
        raise ValueError("Silver counts, primary key or target totals mismatch")
    invalid = (F.col("source_dataset").isNull() | (F.col("source_dataset") != "train")
               | F.col("source_sha256").isNull() | (F.col("source_sha256") != EXPECTED["source_sha256"])
               | F.col("Will_Buy_EV").isNull() | ~F.col("Will_Buy_EV").isin("Yes", "No")
               | F.col("will_buy_ev_flag").isNull()
               | (F.col("will_buy_ev_flag") != F.when(F.col("Will_Buy_EV") == "Yes", 1).otherwise(0)))
    if source.where(invalid).limit(1).count():
        raise ValueError("Invalid source lineage or target mapping")

    gold_run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    fact = source
    for name, band in SPEC["bands"].items():
        fact = fact.withColumn(name, F.expr(band_sql(band)))
    fact = fact.withColumn("silver_run_id", F.lit(SPEC["silver_run_id"])).withColumn("gold_run_id", F.lit(gold_run_id)).cache()

    def summarize(frame, groups):
        summary = frame.groupBy(*groups).agg(F.count("*").alias("respondent_count"), F.sum("will_buy_ev_flag").alias("yes_count"))
        return summary.withColumn("no_count", F.col("respondent_count") - F.col("yes_count")).withColumn("purchase_intent_rate", F.col("yes_count") / F.col("respondent_count"))

    kpi = summarize(fact, []).withColumn("source_dataset", F.lit("train"))
    segments = []
    for dimension in SPEC["segments"]:
        segment = summarize(fact, [dimension]).withColumnRenamed(dimension, "segment_value")
        segments.append(segment.withColumn("segment_value", F.col("segment_value").cast("string")).withColumn("segment_dimension", F.lit(dimension)))
    segment_summary = reduce(lambda left, right: left.unionByName(right), segments).cache()
    actual = {(r.segment_dimension, r.segment_value): (r.respondent_count, r.yes_count) for r in segment_summary.collect()}
    expected = {(r["segment_dimension"], r["segment_value"]): (r["respondent_count"], r["yes_count"]) for r in EXPECTED["segments"]}
    if actual != expected:
        raise ValueError("Gold segment counts differ from the independent local reference")
    for name in SPEC["bands"]:
        if fact.where(F.col(name) == "Unknown").limit(1).count():
            raise ValueError(f"Unexpected null/unknown band: {name}")
    for name in SPEC["segments"]:
        if fact.where(F.col(name).isNull()).limit(1).count():
            raise ValueError(f"Null segment: {name}")

    tables = {"fact_ev_purchase_intent": fact, "agg_ev_kpi": kpi, "agg_ev_segments": segment_summary}
    outputs = []
    for role, frame in tables.items():
        if role != "fact_ev_purchase_intent":
            frame = frame.withColumn("silver_run_id", F.lit(SPEC["silver_run_id"])).withColumn("gold_run_id", F.lit(gold_run_id))
        name = f"{role}_{gold_run_id.lower()}"
        table = name
        expected_rows = EXPECTED["respondent_count"] if role == "fact_ev_purchase_intent" else (1 if role == "agg_ev_kpi" else len(expected))
        frame.write.format("delta").mode("errorifexists").saveAsTable(table)
        written = spark.table(table)
        if written.count() != expected_rows:
            raise ValueError(f"Written row count mismatch: {table}")
        if role == "fact_ev_purchase_intent":
            if written.select("id").distinct().count() != expected_rows or written.agg(F.sum("will_buy_ev_flag")).first()[0] != EXPECTED["yes_count"]:
                raise ValueError("Written fact key/target mismatch")
        elif role == "agg_ev_segments":
            readback = {(r.segment_dimension, r.segment_value): (r.respondent_count, r.yes_count) for r in written.collect()}
            if readback != expected:
                raise ValueError("Written segment reconciliation failed")
        else:
            row = written.first()
            if (row.respondent_count, row.yes_count, row.no_count) != (EXPECTED["respondent_count"], EXPECTED["yes_count"], EXPECTED["no_count"]):
                raise ValueError("Written KPI reconciliation failed")
        outputs.append({"role": role, "table": table, "rows": expected_rows})

    result = {"status": "published", "run_id": gold_run_id, "silver_run_id": SPEC["silver_run_id"], "silver_delta_version": 0, "pipeline_run_id": pipeline_run_id,
              "respondent_count": EXPECTED["respondent_count"], "yes_count": EXPECTED["yes_count"], "purchase_intent_rate": EXPECTED["purchase_intent_rate"], "tables": outputs}
    marker = Path(f"/lakehouse/default/Files/quality/{gold_run_id}_published.json")
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps(result, indent=2), encoding="utf-8")
    source.unpersist()
    fact.unpersist()
    segment_summary.unpersist()
    return result

result = execute_gold(gold_run_id)
print(json.dumps(result, indent=2))
