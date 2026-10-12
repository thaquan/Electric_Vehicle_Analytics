# Databricks notebook source
import json
import hashlib
import sys
from pathlib import Path
from pyspark.sql import SparkSession

dbutils.widgets.text('project_root', '/Volumes/workspace/ev_phase11/ev_phase11/project')
PROJECT_ROOT = Path(dbutils.widgets.get('project_root'))
package = json.loads((PROJECT_ROOT / 'package_manifest.json').read_text(encoding='utf-8'))
required = {f'src/{name}.py' for name in ('__init__', 'bronze', 'silver', 'gold',
            'quality_checks', 'run_contract', 'runtime', 'stage_runner', 'run_pipeline')}
required.update({'scripts/bronze_silver.py', 'scripts/gold_rules.py', 'scripts/star_schema.py',
                 'metadata/source_manifest.json', 'metadata/categorical_profile.json',
                 'metadata/profiling_summary.json', 'metadata/gold_spec.json',
                 'metadata/gold_expected_metrics.json', 'metadata/star_expected_metrics.json'})
if (package.get('version') != 2 or package.get('platform') != 'databricks-serverless'
        or package.get('runtime_source') != 'shared-src' or not required.issubset(package['files'])):
    raise RuntimeError('Build a new shared-runtime package with scripts/phase11_package.py')
for relative, expected in package['files'].items():
    path = PROJECT_ROOT / relative
    if not path.resolve().is_relative_to(PROJECT_ROOT.resolve()):
        raise RuntimeError(f'Invalid package path: {relative}')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != expected['sha256'] or path.stat().st_size != expected['bytes']:
        raise RuntimeError(f'Package checksum mismatch: {relative}')
sys.path.insert(0, str(PROJECT_ROOT))
# A notebook may be rerun in a Python session that imported a different release.
for name in list(sys.modules):
    if (name in ('src', 'scripts', 'gold_rules', 'star_schema')
            or name.startswith(('src.', 'scripts.'))):
        del sys.modules[name]

from src.run_pipeline import execute_pipeline, utc_run_id


def platform_session(stage):
    # Reuse the platform's session. Never set local[*], cache or stop it.
    session = globals().get('spark')
    if session is None:
        session = SparkSession.getActiveSession()
    if session is None:
        raise RuntimeError('No active Databricks Spark session')
    session.conf.set('spark.sql.ansi.enabled', 'true')
    session.conf.set('spark.sql.session.timeZone', 'UTC')
    return session


report = execute_pipeline(
    PROJECT_ROOT / 'data/raw/kaggle', PROJECT_ROOT / 'metadata',
    PROJECT_ROOT / 'output/phase11', 'phase11_' + utc_run_id(),
    runtime='databricks-serverless', session_factory=platform_session)
print(json.dumps(report, indent=2))
