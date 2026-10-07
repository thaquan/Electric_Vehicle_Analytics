# Databricks notebook source
import json
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from pyspark.sql import SparkSession

dbutils.widgets.text('project_root', '/Volumes/workspace/ev_phase11/ev_phase11/project')
PROJECT_ROOT = Path(dbutils.widgets.get('project_root'))
package = json.loads((PROJECT_ROOT / 'package_manifest.json').read_text(encoding='utf-8'))
expected_overlay = {f'src/{name}.py': f'databricks/runtime_src/{name}.py'
                    for name in ('bronze', 'silver', 'gold', 'quality_checks')}
if package.get('platform') != 'databricks-serverless' or package.get('runtime_overlay') != expected_overlay:
    raise RuntimeError('Build the serverless project with scripts/phase11_package.py')
if not set(expected_overlay).issubset(package['files']):
    raise RuntimeError('Package manifest is missing runtime modules')
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
    if name == 'src' or name.startswith('src.') or name in ('gold_rules', 'star_schema'):
        del sys.modules[name]

from src.bronze import build_bronze
from src.silver import build_silver
from src.gold import build_gold
from src.quality_checks import verify_gold
from src.run_contract import run_directory, bind_context, inventory

raw_dir = PROJECT_ROOT / 'data/raw/kaggle'
metadata_dir = PROJECT_ROOT / 'metadata'
output_root = PROJECT_ROOT / 'output/phase11'
run_id = datetime.now(timezone.utc).strftime('phase11_%Y%m%dT%H%M%SZ')
run_dir = run_directory(output_root, run_id)
if run_dir.exists():
    raise ValueError(f'Run directory already exists: {run_dir}')
run_dir.mkdir(parents=True)
bind_context(run_dir, raw_dir, metadata_dir)

# Databricks serverless already provides a Spark Connect session.
# Reuse it instead of configuring local[*], which is only valid for Phase 10 local Spark.
spark = globals().get('spark') or SparkSession.getActiveSession()
if spark is None:
    raise RuntimeError('No active Databricks Spark session')
spark.conf.set('spark.sql.ansi.enabled', 'true')
spark.conf.set('spark.sql.session.timeZone', 'UTC')

report = {
    'status': 'failed',
    'run_id': run_id,
    'platform': 'databricks-serverless',
    'started_at_utc': datetime.now(timezone.utc).isoformat(),
    'run_dir': str(run_dir),
}
try:
    processed_at = datetime.now(timezone.utc).isoformat()
    report['bronze'] = build_bronze(spark, raw_dir, metadata_dir, run_dir / 'bronze')
    report['silver'] = build_silver(spark, run_dir / 'bronze', metadata_dir, run_dir / 'silver', run_id, processed_at)
    report['gold'] = build_gold(spark, run_dir / 'silver', metadata_dir, run_dir / 'gold', run_id, run_id)
    artifacts = inventory(run_dir, ['run_context.json', 'bronze', 'silver', 'gold'])
    report['quality'] = verify_gold(spark, run_dir / 'gold', metadata_dir)
    if inventory(run_dir, ['run_context.json', 'bronze', 'silver', 'gold']) != artifacts:
        raise RuntimeError('Artifacts changed during quality checks')
    marker = {
        'status': 'published',
        'run_id': run_id,
        'published_at_utc': datetime.now(timezone.utc).isoformat(),
        'quality': report['quality'],
        'artifacts': artifacts,
    }
    (run_dir / 'published.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
    report['status'] = 'passed'
finally:
    report['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
    (run_dir / 'run_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')

print(json.dumps(report, indent=2))
