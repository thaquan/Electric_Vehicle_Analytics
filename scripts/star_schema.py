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
