# Databricks notebook source
import json
from datetime import datetime, timezone
from pathlib import Path

report = {'captured_at_utc': datetime.now(timezone.utc).isoformat(), 'spark_version': spark.version}
queries = {
    'identity': 'SELECT current_user() AS principal, current_catalog() AS catalog',
    'billing_usage': """SELECT usage_metadata.job_id AS job_id, sku_name, usage_unit,
        sum(usage_quantity) AS net_usage_quantity, min(usage_start_time) AS first_usage,
        max(usage_end_time) AS last_usage, count(*) AS billing_records
        FROM system.billing.usage
        WHERE usage_start_time >= current_timestamp() - INTERVAL 7 DAYS
          AND usage_metadata.job_id IN ('149867914773886', '183474134559346')
        GROUP BY usage_metadata.job_id, sku_name, usage_unit""",
}
for name, sql in queries.items():
    try:
        report[name] = [r.asDict(recursive=True) for r in spark.sql(sql).collect()]
    except Exception as exc:
        report[name + '_error'] = str(exc)
report['cost_note'] = 'Usage units only; no monetary cost inferred from missing usage or unverified pricing.'
out = Path('/Volumes/workspace/ev_phase11/ev_phase11/releases/review_20261006/project/metadata/phase12/runtime_billing.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
print(json.dumps(report, indent=2, default=str))
