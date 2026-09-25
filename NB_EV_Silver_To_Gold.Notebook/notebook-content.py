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
STAR_EXPECTED = json.loads('{"gold_schema_version": 2, "verification_scope": "Full local train snapshot: pandas reconstruction and SQLite SQL; not Fabric execution", "source_sha256": "141B8AC4B171CEBCE17EA7F52CF5C26F1AC5B675C24850096A3CFACA60B036D4", "fact_rows": 668665, "dimension_rows": {"dim_demographics": 45, "dim_income": 4, "dim_mobility": 16, "dim_charging": 2, "dim_attitude_incentive": 30}, "reconstruction": "passed", "orphan_keys": 0, "kpi_sql": {"respondent_count": 668665, "yes_count": 116779, "no_count": 551886, "purchase_intent_rate": 0.17464500160768098}, "segments_sql": [{"segment_dimension": "age_band", "segment_value": "35-44", "respondent_count": 151968, "yes_count": 26401, "no_count": 125567, "purchase_intent_rate": 0.17372736365550642}, {"segment_dimension": "age_band", "segment_value": "45-54", "respondent_count": 154375, "yes_count": 28321, "no_count": 126054, "purchase_intent_rate": 0.18345587044534412}, {"segment_dimension": "age_band", "segment_value": "55-64", "respondent_count": 146413, "yes_count": 25428, "no_count": 120985, "purchase_intent_rate": 0.1736731027982488}, {"segment_dimension": "age_band", "segment_value": "65+", "respondent_count": 73568, "yes_count": 11692, "no_count": 61876, "purchase_intent_rate": 0.15892779469334492}, {"segment_dimension": "age_band", "segment_value": "Under 35", "respondent_count": 142341, "yes_count": 24937, "no_count": 117404, "purchase_intent_rate": 0.17519196858248853}, {"segment_dimension": "income_band", "segment_value": "100k+", "respondent_count": 182731, "yes_count": 53325, "no_count": 129406, "purchase_intent_rate": 0.29182240561262185}, {"segment_dimension": "income_band", "segment_value": "50k-<75k", "respondent_count": 159595, "yes_count": 16599, "no_count": 142996, "purchase_intent_rate": 0.1040070177637144}, {"segment_dimension": "income_band", "segment_value": "75k-<100k", "respondent_count": 251563, "yes_count": 43600, "no_count": 207963, "purchase_intent_rate": 0.17331642570648306}, {"segment_dimension": "income_band", "segment_value": "Under 50k", "respondent_count": 74776, "yes_count": 3255, "no_count": 71521, "purchase_intent_rate": 0.04353000962875789}, {"segment_dimension": "commute_band", "segment_value": "10-<25 km", "respondent_count": 86826, "yes_count": 18410, "no_count": 68416, "purchase_intent_rate": 0.21203326192615116}, {"segment_dimension": "commute_band", "segment_value": "25-<50 km", "respondent_count": 303373, "yes_count": 52001, "no_count": 251372, "purchase_intent_rate": 0.17140945304954627}, {"segment_dimension": "commute_band", "segment_value": "50+ km", "respondent_count": 132507, "yes_count": 19445, "no_count": 113062, "purchase_intent_rate": 0.1467469643113194}, {"segment_dimension": "commute_band", "segment_value": "Under 10 km", "respondent_count": 145959, "yes_count": 26923, "no_count": 119036, "purchase_intent_rate": 0.18445590885111574}, {"segment_dimension": "Gender", "segment_value": "Female", "respondent_count": 295427, "yes_count": 52480, "no_count": 242947, "purchase_intent_rate": 0.17764117700819493}, {"segment_dimension": "Gender", "segment_value": "Male", "respondent_count": 367954, "yes_count": 63381, "no_count": 304573, "purchase_intent_rate": 0.17225250982459764}, {"segment_dimension": "Gender", "segment_value": "Other", "respondent_count": 5284, "yes_count": 918, "no_count": 4366, "purchase_intent_rate": 0.1737320211960636}, {"segment_dimension": "City_Type", "segment_value": "Rural", "respondent_count": 123983, "yes_count": 23977, "no_count": 100006, "purchase_intent_rate": 0.1933894162909431}, {"segment_dimension": "City_Type", "segment_value": "Suburban", "respondent_count": 255377, "yes_count": 46207, "no_count": 209170, "purchase_intent_rate": 0.1809364194896173}, {"segment_dimension": "City_Type", "segment_value": "Urban", "respondent_count": 289305, "yes_count": 46595, "no_count": 242710, "purchase_intent_rate": 0.1610583985758974}, {"segment_dimension": "Current_Car_Type", "segment_value": "Hatchback", "respondent_count": 79438, "yes_count": 13846, "no_count": 65592, "purchase_intent_rate": 0.17429945366197538}, {"segment_dimension": "Current_Car_Type", "segment_value": "SUV", "respondent_count": 246545, "yes_count": 44613, "no_count": 201932, "purchase_intent_rate": 0.18095276724330245}, {"segment_dimension": "Current_Car_Type", "segment_value": "Sedan", "respondent_count": 303459, "yes_count": 52185, "no_count": 251274, "purchase_intent_rate": 0.17196721797672831}, {"segment_dimension": "Current_Car_Type", "segment_value": "Truck", "respondent_count": 39223, "yes_count": 6135, "no_count": 33088, "purchase_intent_rate": 0.15641332891415752}, {"segment_dimension": "Home_Charging_Possible", "segment_value": "No", "respondent_count": 205988, "yes_count": 26178, "no_count": 179810, "purchase_intent_rate": 0.12708507291686894}, {"segment_dimension": "Home_Charging_Possible", "segment_value": "Yes", "respondent_count": 462677, "yes_count": 90601, "no_count": 372076, "purchase_intent_rate": 0.1958191135500576}, {"segment_dimension": "Subsidy_Available", "segment_value": "No", "respondent_count": 248756, "yes_count": 1432, "no_count": 247324, "purchase_intent_rate": 0.0057566450658476575}, {"segment_dimension": "Subsidy_Available", "segment_value": "Yes", "respondent_count": 419909, "yes_count": 115347, "no_count": 304562, "purchase_intent_rate": 0.2746952315858912}, {"segment_dimension": "Range_Anxiety_Level", "segment_value": "High", "respondent_count": 2194, "yes_count": 3, "no_count": 2191, "purchase_intent_rate": 0.0013673655423883319}, {"segment_dimension": "Range_Anxiety_Level", "segment_value": "Low", "respondent_count": 603972, "yes_count": 114167, "no_count": 489805, "purchase_intent_rate": 0.18902697476041935}, {"segment_dimension": "Range_Anxiety_Level", "segment_value": "Medium", "respondent_count": 62499, "yes_count": 2609, "no_count": 59890, "purchase_intent_rate": 0.04174466791468664}, {"segment_dimension": "Environmental_Concern_Level", "segment_value": "1.0", "respondent_count": 147476, "yes_count": 834, "no_count": 146642, "purchase_intent_rate": 0.00565515744934769}, {"segment_dimension": "Environmental_Concern_Level", "segment_value": "2.0", "respondent_count": 135133, "yes_count": 2889, "no_count": 132244, "purchase_intent_rate": 0.02137893778721704}, {"segment_dimension": "Environmental_Concern_Level", "segment_value": "3.0", "respondent_count": 127351, "yes_count": 14126, "no_count": 113225, "purchase_intent_rate": 0.11092178310339142}, {"segment_dimension": "Environmental_Concern_Level", "segment_value": "4.0", "respondent_count": 130469, "yes_count": 32467, "no_count": 98002, "purchase_intent_rate": 0.2488483854402195}, {"segment_dimension": "Environmental_Concern_Level", "segment_value": "5.0", "respondent_count": 128236, "yes_count": 66463, "no_count": 61773, "purchase_intent_rate": 0.5182865965875417}]}')

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
        version = marker.get("gold_schema_version", 1)
        if version not in (1, 2):
            raise ValueError("Unsupported Gold schema version")
        if version == 2:
            roles = {"dim_demographics", "dim_income", "dim_mobility", "dim_charging", "dim_attitude_incentive"}
            counts = marker.get("dimension_rows", {})
            if set(counts) != roles or any(type(n) is not int or not 0 < n <= 668665 for n in counts.values()):
                raise ValueError("Invalid star dimension manifest")
            expected.update({f"{role}_{suffix}": n for role, n in counts.items()})
            if marker.get("star_validation", {}).get("status") != "passed" or marker.get("sql_validation", {}).get("status") != "passed":
                raise ValueError("Gold star/SQL verification missing")
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

"""Gold v2 star contract. Spark dependencies are imported only at runtime."""
import hashlib
import json

STAR_VERSION = 2
DIMENSIONS = [
    {"role": "dim_demographics", "model": "Demographics", "key": "demographics_key",
     "attributes": ["age_band", "Gender", "City_Type"]},
    {"role": "dim_income", "model": "Income", "key": "income_key", "attributes": ["income_band"]},
    {"role": "dim_mobility", "model": "Mobility", "key": "mobility_key",
     "attributes": ["commute_band", "Current_Car_Type"]},
    {"role": "dim_charging", "model": "Charging", "key": "charging_key",
     "attributes": ["Home_Charging_Possible"]},
    {"role": "dim_attitude_incentive", "model": "Attitude and Incentive", "key": "attitude_incentive_key",
     "attributes": ["Environmental_Concern_Level", "Subsidy_Available", "Range_Anxiety_Level"]},
]
FACT_ROLE = "fact_ev_purchase_intent"
FACT_VALUES = ["id", "Age", "Annual_Income_USD", "Daily_Commute_km", "Number_of_Cars_Owned",
               "Charging_Stations_Near_Home", "Charging_Stations_Near_Work", "Will_Buy_EV", "will_buy_ev_flag",
               "source_dataset", "source_file", "source_sha256", "processed_at_utc", "record_key"]
LINEAGE = ["silver_run_id", "gold_run_id"]


def dimension_key(role, values):
    """Portable stable key: UTF-8 SHA256 of a compact JSON array of strings."""
    if any(not isinstance(v, str) for v in values):
        raise ValueError("Dimension attributes must be non-null strings")
    payload = json.dumps([role, *values], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_star_spark(enriched, bands):
    from pyspark.sql import functions as F
    fact = enriched
    tables = {}
    for d in DIMENSIONS:
        attrs, key, role = d["attributes"], d["key"], d["role"]
        invalid = F.lit(False)
        for attr in attrs:
            invalid = invalid | F.col(attr).isNull()
        if enriched.where(invalid).limit(1).count():
            raise ValueError(f"Null dimension attribute: {role}")
        expression = F.sha2(F.to_json(F.array(F.lit(role), *[F.col(a).cast("string") for a in attrs])), 256)
        fact = fact.withColumn(key, expression)
        dimension = fact.select(key, *attrs, *LINEAGE).distinct()
        for attr in attrs:
            if attr in bands:
                values = bands[attr]["labels"]
                mapping = F.create_map(*[v for i, label in enumerate(values) for v in (F.lit(label), F.lit(i + 1))])
                dimension = dimension.withColumn(attr + "_sort", mapping[F.col(attr)])
        tables[role] = dimension
    tables[FACT_ROLE] = fact.select(*FACT_VALUES, *[d["key"] for d in DIMENSIONS], *LINEAGE)
    return tables


def verify_star_spark(tables, enriched, bands, expected_dimensions):
    """Verify written Delta data, then losslessly reconstruct every source column."""
    from pyspark.sql import functions as F
    fact = tables[FACT_ROLE]
    count = enriched.count()
    if fact.count() != count or fact.select("id").distinct().count() != count or fact.where("id IS NULL").limit(1).count():
        raise ValueError("Fact grain/key mismatch")
    restored = fact
    counts = {}
    for d in DIMENSIONS:
        role, key, attrs = d["role"], d["key"], d["attributes"]
        dim = tables[role]
        n = dim.count()
        if n != expected_dimensions[role] or dim.select(key).distinct().count() != n:
            raise ValueError(f"Dimension cardinality/key mismatch: {role}")
        if dim.select(*attrs).distinct().count() != n:
            raise ValueError(f"Duplicate dimension business attributes: {role}")
        invalid = F.col(key).isNull()
        for attr in attrs:
            invalid = invalid | F.col(attr).isNull()
        computed_key = F.sha2(F.to_json(F.array(F.lit(role), *[F.col(a).cast("string") for a in attrs])), 256)
        invalid = invalid | (F.col(key) != computed_key)
        for attr in attrs:
            if attr in bands:
                mapping = F.create_map(*[v for i, label in enumerate(bands[attr]["labels"]) for v in (F.lit(label), F.lit(i + 1))])
                invalid = invalid | F.col(attr + "_sort").isNull() | mapping[F.col(attr)].isNull() | (F.col(attr + "_sort") != mapping[F.col(attr)])
        if dim.where(invalid).limit(1).count():
            raise ValueError(f"Invalid dimension key/attribute/sort: {role}")
        if fact.where(F.col(key).isNull()).limit(1).count() or fact.join(dim.select(key), key, "left_anti").limit(1).count():
            raise ValueError(f"Orphan fact foreign key: {role}")
        restored = restored.join(dim.select(key, *attrs), key, "inner")
        counts[role] = n
    columns = enriched.columns
    restored = restored.select(*columns)
    if restored.count() != count or restored.exceptAll(enriched.select(*columns)).limit(1).count() or enriched.select(*columns).exceptAll(restored).limit(1).count():
        raise ValueError("Star reconstruction differs from Silver (lost, duplicated or changed data)")
    return {"status": "passed", "fact_rows": count, "dimension_rows": counts,
            "orphan_keys": 0, "silver_reconstruction": "exact", "gold_schema_version": STAR_VERSION}

"""Shared read-only SQL for Spark, SQLite reference tests and Fabric T-SQL."""
import re


def sql_identifier(value):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", value):
        raise ValueError(f"Unsafe SQL identifier: {value!r}")
    return value


def star_queries(table_names, dimensions, segments):
    # Table names may be explicitly qualified by the caller. Validate every part.
    for name in table_names.values():
        for part in name.split("."):
            sql_identifier(part)
    fact = table_names["fact_ev_purchase_intent"]
    metrics = ("COUNT(*) AS respondent_count, SUM(f.will_buy_ev_flag) AS yes_count, "
               "COUNT(*) - SUM(f.will_buy_ev_flag) AS no_count, "
               "1.0 * SUM(f.will_buy_ev_flag) / NULLIF(COUNT(*), 0) AS purchase_intent_rate")
    kpi = f"SELECT {metrics} FROM {fact} f"
    queries = []
    for attr in segments:
        sql_identifier(attr)
        d = next(d for d in dimensions if attr in d["attributes"])
        queries.append(f"SELECT '{attr}' AS segment_dimension, d.{attr} AS segment_value, {metrics} "
                       f"FROM {fact} f JOIN {table_names[d['role']]} d ON f.{d['key']} = d.{d['key']} GROUP BY d.{attr}")
    return {"kpi": kpi, "segments": "\nUNION ALL\n".join(queries)}


def check_sql_results(kpi, rows, expected):
    counts = (int(kpi["respondent_count"]), int(kpi["yes_count"]), int(kpi["no_count"]))
    if counts != (expected["respondent_count"], expected["yes_count"], expected["no_count"]):
        raise ValueError("SQL KPI counts do not reconcile")
    if abs(float(kpi["purchase_intent_rate"]) - expected["purchase_intent_rate"]) > 1e-6:
        raise ValueError("SQL KPI rate does not reconcile")
    actual = {(r["segment_dimension"], r["segment_value"]): (int(r["respondent_count"]), int(r["yes_count"])) for r in rows}
    target = {(r["segment_dimension"], r["segment_value"]): (r["respondent_count"], r["yes_count"]) for r in expected["segments"]}
    if len(rows) != len(target) or actual != target:
        raise ValueError("SQL segment counts do not reconcile")
    for r in rows:
        if int(r["no_count"]) != int(r["respondent_count"]) - int(r["yes_count"]):
            raise ValueError("SQL segment No count mismatch")
        if abs(float(r["purchase_intent_rate"]) - int(r["yes_count"]) / int(r["respondent_count"])) > 1e-6:
            raise ValueError("SQL segment rate mismatch")


def endpoint_sql(table_names, dimensions, segments, silver_table):
    queries = star_queries({r: 'dbo.' + n for r, n in table_names.items()}, dimensions, segments)
    sql_identifier(silver_table)
    fact = 'dbo.' + table_names['fact_ev_purchase_intent']
    assertions = []
    for d in dimensions:
        key, table = d['key'], 'dbo.' + table_names[d['role']]
        assertions.append(f"SELECT '{d['role']}' AS dimension_name, COUNT(*) AS orphan_count FROM {fact} f LEFT JOIN {table} d ON f.{key}=d.{key} WHERE d.{key} IS NULL;")
        assertions.append(f"SELECT {key}, COUNT(*) AS duplicate_count FROM {table} GROUP BY {key} HAVING COUNT(*) > 1 OR {key} IS NULL;")
    attributes = [(f"d{i}", attr) for i, d in enumerate(dimensions) for attr in d['attributes'] if not attr.endswith('_band')]
    measures = ['Age', 'Annual_Income_USD', 'Daily_Commute_km', 'Number_of_Cars_Owned',
                'Charging_Stations_Near_Home', 'Charging_Stations_Near_Work', 'Will_Buy_EV', 'will_buy_ev_flag']
    joins = ' '.join(f"LEFT JOIN dbo.{table_names[d['role']]} d{i} ON f.{d['key']}=d{i}.{d['key']}" for i,d in enumerate(dimensions))
    differences = [f'f.{c} <> s.{c} OR f.{c} IS NULL OR s.{c} IS NULL' for c in measures]
    differences += [f'{alias}.{attr} <> s.{attr} OR {alias}.{attr} IS NULL OR s.{attr} IS NULL' for alias,attr in attributes]
    return ("-- Run on LH_EV_Gold SQL analytics endpoint after SQL metadata synchronization.\n"
            "-- These statements are read-only; all orphan/duplicate result counts must be zero.\n"
            + queries['kpi'] + ";\n\n" + queries['segments'] + ";\n\n" + '\n'.join(assertions)
            + f"\n\n-- Expected 0 rows: compare every original business field with Silver.\n"
            + f"SELECT COALESCE(f.id,s.id) AS mismatched_id FROM {fact} f {joins} FULL OUTER JOIN LH_EV_Silver.dbo.{silver_table} s ON f.id=s.id WHERE f.id IS NULL OR s.id IS NULL OR "
            + ' OR '.join(differences) + ';\n')

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
            if (row.respondent_count, row.yes_count, row.no_count) != (expected_metrics["respondent_count"], expected_metrics["yes_count"], expected_metrics["no_count"]):
                raise ValueError("Published KPI mismatch")
            if abs(row.purchase_intent_rate - expected_metrics["purchase_intent_rate"]) > 1e-12:
                raise ValueError("Published KPI rate mismatch")
        elif name.startswith("agg_ev_segments_"):
            expected = {(r["segment_dimension"], r["segment_value"]): (r["respondent_count"], r["yes_count"]) for r in expected_metrics["segments"]}
            actual = {(r.segment_dimension, r.segment_value): (r.respondent_count, r.yes_count) for r in frame.collect()}
            if actual != expected:
                raise ValueError("Published segment mismatch")


def verify_gold_star(spark, root_uri, marker, silver_uri, spec, expected, star_expected):
    """Re-read immutable Delta version 0; verify joins and execute SQL independently."""
    source = spark.read.format("delta").option("versionAsOf", 0).load(f"{silver_uri}/{spec['source_relative_path']}")
    for name, band in spec["bands"].items():
        source = source.withColumn(name, F.expr(band_sql(band)))
    source = source.withColumn("silver_run_id", F.lit(marker["silver_run_id"])).withColumn("gold_run_id", F.lit(marker["run_id"]))
    tables = {e["role"]: spark.read.format("delta").option("versionAsOf", 0).load(f"{root_uri}/Tables/{e['table']}") for e in marker["tables"]}
    star = verify_star_spark(tables, source, spec["bands"], star_expected["dimension_rows"])
    # Register only the explicitly selected snapshot; SQL never reads a stale run.
    names = {}
    for role, frame in tables.items():
        name = "verify_" + role
        frame.createOrReplaceTempView(name)
        names[role] = name
    try:
        queries = star_queries(names, DIMENSIONS, spec["segments"])
        kpi = spark.sql(queries["kpi"]).first().asDict()
        segments = [r.asDict() for r in spark.sql(queries["segments"]).collect()]
        check_sql_results(kpi, segments, expected)
        silver_row = source.agg(F.count("*").alias("n"), F.sum("will_buy_ev_flag").alias("yes")).first()
        if (kpi["respondent_count"], kpi["yes_count"]) != (silver_row.n, silver_row.yes):
            raise ValueError("SQL Gold totals differ from selected Silver")
        return {"star_validation": star, "sql_validation": {"status": "passed", "engine": "Spark SQL",
                "respondent_count": int(kpi["respondent_count"]), "yes_count": int(kpi["yes_count"]),
                "no_count": int(kpi["no_count"]), "purchase_intent_rate": float(kpi["purchase_intent_rate"]), "segment_groups": len(segments)}}
    finally:
        for name in names.values():
            spark.catalog.dropTempView(name)


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
        if gold_marker.get("gold_schema_version") != STAR_VERSION:
            raise ValueError("Current pipeline requires Gold star schema v2; rerun Build_Gold")
        verify_published_tables(spark, gold_uri, gold_marker, "gold", EXPECTED)
        checks = verify_gold_star(spark, gold_uri, gold_marker, silver_uri, SPEC, EXPECTED, STAR_EXPECTED)
        result = {"status": "verified", "stage": "e2e", "pipeline_run_id": pipeline_run_id, "silver_run_id": SPEC["silver_run_id"], "gold_run_id": input_gold_run_id, "tables": gold_marker["tables"], "gold_schema_version": STAR_VERSION, **checks}
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

    tables = build_star_spark(fact, SPEC["bands"])
    tables.update({"agg_ev_kpi": kpi, "agg_ev_segments": segment_summary})
    outputs = []
    for role, frame in tables.items():
        if role != "fact_ev_purchase_intent":
            frame = frame.withColumn("silver_run_id", F.lit(SPEC["silver_run_id"])).withColumn("gold_run_id", F.lit(gold_run_id))
        name = f"{role}_{gold_run_id.lower()}"
        table = name
        expected_rows = (EXPECTED["respondent_count"] if role == "fact_ev_purchase_intent" else
                         STAR_EXPECTED["dimension_rows"][role] if role.startswith("dim_") else
                         1 if role == "agg_ev_kpi" else len(expected))
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
        elif role == "agg_ev_kpi":
            row = written.first()
            if (row.respondent_count, row.yes_count, row.no_count) != (EXPECTED["respondent_count"], EXPECTED["yes_count"], EXPECTED["no_count"]):
                raise ValueError("Written KPI reconciliation failed")
        outputs.append({"role": role, "table": table, "rows": expected_rows,
                        "columns": [{"name": f.name, "type": f.dataType.simpleString()} for f in written.schema.fields]})

    result = {"status": "published", "run_id": gold_run_id, "silver_run_id": SPEC["silver_run_id"], "silver_delta_version": 0, "pipeline_run_id": pipeline_run_id,
              "respondent_count": EXPECTED["respondent_count"], "yes_count": EXPECTED["yes_count"], "purchase_intent_rate": EXPECTED["purchase_intent_rate"], "tables": outputs,
              "gold_schema_version": STAR_VERSION, "dimension_rows": STAR_EXPECTED["dimension_rows"]}
    gold_uri = f"abfss://{CONFIG['workspace_id']}@onelake.dfs.fabric.microsoft.com/{CONFIG['gold_lakehouse_id']}"
    verify_published_tables(spark, gold_uri, result, "gold", EXPECTED)
    result.update(verify_gold_star(spark, gold_uri, result, silver_uri, SPEC, EXPECTED, STAR_EXPECTED))
    require_publication(result, "gold", gold_run_id, pipeline_run_id, SPEC["silver_run_id"])
    sql_path = Path(f"/lakehouse/default/Files/sql/{gold_run_id}_reconciliation.sql")
    sql_path.parent.mkdir(parents=True, exist_ok=True)
    sql_path.write_text(endpoint_sql({e["role"]: e["table"] for e in outputs}, DIMENSIONS, SPEC["segments"], SPEC["source_table"]), encoding="utf-8")
    result["sql_endpoint_validation"] = "pending: execute the generated T-SQL on the Gold SQL analytics endpoint"
    result["sql_script_path"] = f"Files/sql/{gold_run_id}_reconciliation.sql"
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
