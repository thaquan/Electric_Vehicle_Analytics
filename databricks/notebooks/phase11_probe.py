# Databricks notebook source
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from pyspark.sql import SparkSession

spark = globals().get('spark') or SparkSession.getActiveSession()
if spark is None:
    raise RuntimeError('No active Databricks Spark session')

report = {
    'captured_at_utc': datetime.now(timezone.utc).isoformat(),
    'compute': 'databricks-serverless',
    'spark_version': spark.version,
    'python_version': sys.version,
}
try:
    report['sql_version'] = spark.sql('SELECT version() AS v').first()['v']
except Exception as exc:
    report['sql_version_error'] = str(exc)

try:
    rows = spark.sql("""
        SELECT sku_name, usage_quantity, usage_unit, usage_start_time, usage_end_time,
               usage_metadata.job_id AS job_id
        FROM system.billing.usage
        WHERE usage_start_time >= current_timestamp() - INTERVAL 1 DAY
          AND usage_metadata.job_id = '149867914773886'
        ORDER BY usage_start_time DESC
    """).collect()
    report['billing_usage_rows'] = [r.asDict(recursive=True) for r in rows]
except Exception as exc:
    report['billing_usage_error'] = str(exc)

out = Path('/Volumes/workspace/ev_phase11/ev_phase11/project/metadata/phase11/runtime_billing_probe.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2, default=str), encoding='utf-8')
print(json.dumps(report, indent=2, default=str))