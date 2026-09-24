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
