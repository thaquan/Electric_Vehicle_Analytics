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
