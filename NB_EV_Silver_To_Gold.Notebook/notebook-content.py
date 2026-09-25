# Fabric notebook source


# CELL ********************

# MAGIC %%configure -f
# MAGIC {
# MAGIC   "defaultLakehouse": {
# MAGIC     "name": "LH_EV_Gold",
# MAGIC     "id": "32e99e91-38e9-4428-8fd2-6bcff6573088",
# MAGIC     "workspaceId": "5fe78794-25c3-41ee-b35e-bc56542d2cea"
# MAGIC   }
# MAGIC }


# PARAMETERS CELL ********************

pipeline_run_id = ""
run_mode = "publish"
silver_run_id = ""
gold_run_id = ""


# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import json
import notebookutils
CONFIG = json.loads('{"workspace_id": "5fe78794-25c3-41ee-b35e-bc56542d2cea", "silver_lakehouse_id": "676ba346-22dd-4eeb-92ec-4f53f09ccca7", "gold_lakehouse_id": "32e99e91-38e9-4428-8fd2-6bcff6573088"}')
DEFAULT_SPEC = json.loads('{"version": 1, "source_dataset": "train", "silver_run_id": "20260924T031507399976Z", "source_table": "silver_train_20260924t031507399976z", "source_relative_path": "Tables/silver_train_20260924t031507399976z", "expected_rows": 668665, "expected_yes": 116779, "bands": {"age_band": {"column": "Age", "edges": [35, 45, 55, 65], "labels": ["Under 35", "35-44", "45-54", "55-64", "65+"]}, "income_band": {"column": "Annual_Income_USD", "edges": [50000, 75000, 100000], "labels": ["Under 50k", "50k-<75k", "75k-<100k", "100k+"]}, "commute_band": {"column": "Daily_Commute_km", "edges": [10, 25, 50], "labels": ["Under 10 km", "10-<25 km", "25-<50 km", "50+ km"]}}, "segments": ["age_band", "income_band", "commute_band", "Gender", "City_Type", "Current_Car_Type", "Home_Charging_Possible", "Subsidy_Available", "Range_Anxiety_Level", "Environmental_Concern_Level"], "metric_definition": "purchase_intent_rate = yes_count / respondent_count; not realized vehicle sales"}')
EXPECTED = json.loads('{"verification_scope": "Local train snapshot reference; not Fabric Gold execution", "source_sha256": "141B8AC4B171CEBCE17EA7F52CF5C26F1AC5B675C24850096A3CFACA60B036D4", "respondent_count": 668665, "yes_count": 116779, "no_count": 551886, "purchase_intent_rate": 0.17464500160768098, "segments": [{"segment_dimension": "age_band", "segment_value": "35-44", "respondent_count": 151968, "yes_count": 26401}, {"segment_dimension": "age_band", "segment_value": "45-54", "respondent_count": 154375, "yes_count": 28321}, {"segment_dimension": "age_band", "segment_value": "55-64", "respondent_count": 146413, "yes_count": 25428}, {"segment_dimension": "age_band", "segment_value": "65+", "respondent_count": 73568, "yes_count": 11692}, {"segment_dimension": "age_band", "segment_value": "Under 35", "respondent_count": 142341, "yes_count": 24937}, {"segment_dimension": "income_band", "segment_value": "100k+", "respondent_count": 182731, "yes_count": 53325}, {"segment_dimension": "income_band", "segment_value": "50k-<75k", "respondent_count": 159595, "yes_count": 16599}, {"segment_dimension": "income_band", "segment_value": "75k-<100k", "respondent_count": 251563, "yes_count": 43600}, {"segment_dimension": "income_band", "segment_value": "Under 50k", "respondent_count": 74776, "yes_count": 3255}, {"segment_dimension": "commute_band", "segment_value": "10-<25 km", "respondent_count": 86826, "yes_count": 18410}, {"segment_dimension": "commute_band", "segment_value": "25-<50 km", "respondent_count": 303373, "yes_count": 52001}, {"segment_dimension": "commute_band", "segment_value": "50+ km", "respondent_count": 132507, "yes_count": 19445}, {"segment_dimension": "commute_band", "segment_value": "Under 10 km", "respondent_count": 145959, "yes_count": 26923}, {"segment_dimension": "Gender", "segment_value": "Female", "respondent_count": 295427, "yes_count": 52480}, {"segment_dimension": "Gender", "segment_value": "Male", "respondent_count": 367954, "yes_count": 63381}, {"segment_dimension": "Gender", "segment_value": "Other", "respondent_count": 5284, "yes_count": 918}, {"segment_dimension": "City_Type", "segment_value": "Rural", "respondent_count": 123983, "yes_count": 23977}, {"segment_dimension": "City_Type", "segment_value": "Suburban", "respondent_count": 255377, "yes_count": 46207}, {"segment_dimension": "City_Type", "segment_value": "Urban", "respondent_count": 289305, "yes_count": 46595}, {"segment_dimension": "Current_Car_Type", "segment_value": "Hatchback", "respondent_count": 79438, "yes_count": 13846}, {"segment_dimension": "Current_Car_Type", "segment_value": "SUV", "respondent_count": 246545, "yes_count": 44613}, {"segment_dimension": "Current_Car_Type", "segment_value": "Sedan", "respondent_count": 303459, "yes_count": 52185}, {"segment_dimension": "Current_Car_Type", "segment_value": "Truck", "respondent_count": 39223, "yes_count": 6135}, {"segment_dimension": "Home_Charging_Possible", "segment_value": "No", "respondent_count": 205988, "yes_count": 26178}, {"segment_dimension": "Home_Charging_Possible", "segment_value": "Yes", "respondent_count": 462677, "yes_count": 90601}, {"segment_dimension": "Subsidy_Available", "segment_value": "No", "respondent_count": 248756, "yes_count": 1432}, {"segment_dimension": "Subsidy_Available", "segment_value": "Yes", "respondent_count": 419909, "yes_count": 115347}, {"segment_dimension": "Range_Anxiety_Level", "segment_value": "High", "respondent_count": 2194, "yes_count": 3}, {"segment_dimension": "Range_Anxiety_Level", "segment_value": "Low", "respondent_count": 603972, "yes_count": 114167}, {"segment_dimension": "Range_Anxiety_Level", "segment_value": "Medium", "respondent_count": 62499, "yes_count": 2609}, {"segment_dimension": "Environmental_Concern_Level", "segment_value": "1.0", "respondent_count": 147476, "yes_count": 834}, {"segment_dimension": "Environmental_Concern_Level", "segment_value": "2.0", "respondent_count": 135133, "yes_count": 2889}, {"segment_dimension": "Environmental_Concern_Level", "segment_value": "3.0", "respondent_count": 127351, "yes_count": 14126}, {"segment_dimension": "Environmental_Concern_Level", "segment_value": "4.0", "respondent_count": 130469, "yes_count": 32467}, {"segment_dimension": "Environmental_Concern_Level", "segment_value": "5.0", "respondent_count": 128236, "yes_count": 66463}]}')

# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

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

"""Band definitions shared by local reference and generated Spark SQL."""
import math
import re
from bisect import bisect_right


def require_gold_context(context, config):
    if (context.get("defaultLakehouseId") != config["gold_lakehouse_id"]
            or context.get("defaultLakehouseWorkspaceId") != config["workspace_id"]):
        raise RuntimeError(f"Expected LH_EV_Gold in WS_EV_Analytics; actual Lakehouse={context.get('defaultLakehouseId')!r}, workspace={context.get('defaultLakehouseWorkspaceId')!r}. Sync the latest notebook and start a fresh run so its first %%configure cell is applied.")


def validate_band(band):
    edges, labels = band["edges"], band["labels"]
    if len(labels) != len(edges) + 1 or edges != sorted(set(edges)):
        raise ValueError("Band edges must increase and have one more label than edges")
    if not all(math.isfinite(float(edge)) for edge in edges):
        raise ValueError("Band edges must be finite")


def band_label(value, band):
    if value is None or not math.isfinite(float(value)):
        return "Unknown"
    return band["labels"][bisect_right(band["edges"], float(value))]


def band_sql(band):
    validate_band(band)
    column = band["column"]
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", column):
        raise ValueError("Invalid source column")
    def quoted(value):
        return "'" + str(value).replace("'", "''") + "'"
    clauses = [f"WHEN `{column}` IS NULL THEN 'Unknown'"]
    clauses += [f"WHEN `{column}` < {edge} THEN {quoted(label)}" for edge, label in zip(band["edges"], band["labels"])]
    return "CASE " + " ".join(clauses) + " ELSE " + quoted(band["labels"][-1]) + " END"

"""Helpers embedded in Gold to independently read published Silver/Gold tables."""
from pyspark.sql import functions as F

def verify_published_tables(spark, root_uri, marker, stage, expected_metrics):
    for entry in marker["tables"]:
        name = entry["table"]
        frame = spark.read.format("delta").option("versionAsOf", 0).load(f"{root_uri}/Tables/{name}")
        if frame.count() != entry["rows"]:
            raise ValueError(f"Published table row mismatch: {name}")
        if stage == "gold":
            invalid_lineage = (F.col("silver_run_id").isNull() | F.col("gold_run_id").isNull()
                               | (F.col("silver_run_id") != marker["silver_run_id"])
                               | (F.col("gold_run_id") != marker["run_id"]))
            if frame.where(invalid_lineage).limit(1).count():
                raise ValueError(f"Published table lineage mismatch: {name}")
        if stage == "silver" or name.startswith("fact_ev_purchase_intent_"):
            key = "Buyer_ID" if name.startswith("silver_original_reference_") else "id"
            if frame.select(key).distinct().count() != entry["rows"] or frame.where(F.col(key).isNull()).limit(1).count():
                raise ValueError(f"Published table key mismatch: {name}")
            if name.startswith("silver_test_"):
                if "Will_Buy_EV" in frame.columns or "will_buy_ev_flag" in frame.columns:
                    raise ValueError("Test target leakage")
            elif name.startswith(("silver_train_", "fact_ev_purchase_intent_")):
                if frame.agg(F.sum("will_buy_ev_flag")).first()[0] != expected_metrics["yes_count"]:
                    raise ValueError("Published train/fact target total mismatch")
        elif name.startswith("agg_ev_kpi_"):
            row = frame.first()
            if (row.respondent_count, row.yes_count, row.no_count) != (668665, 116779, 551886):
                raise ValueError("Published KPI mismatch")
            if abs(row.purchase_intent_rate - expected_metrics["purchase_intent_rate"]) > 1e-12:
                raise ValueError("Published KPI rate mismatch")
        elif name.startswith("agg_ev_segments_"):
            expected = {(r["segment_dimension"], r["segment_value"]): (r["respondent_count"], r["yes_count"]) for r in expected_metrics["segments"]}
            actual = {(r.segment_dimension, r.segment_value): (r.respondent_count, r.yes_count) for r in frame.collect()}
            if actual != expected:
                raise ValueError("Published segment mismatch")


# METADATA ********************
# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

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
