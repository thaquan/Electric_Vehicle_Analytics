from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pyspark.sql import SparkSession

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.bronze import build_bronze
from src.silver import build_silver
from src.gold import build_gold
from src.quality_checks import verify_gold
from src.run_contract import run_directory, bind_context, inventory


def utc_run_id():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, default=ROOT / 'data/raw/kaggle')
    parser.add_argument('--metadata', type=Path, default=ROOT / 'metadata')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'output/phase10')
    parser.add_argument('--run-id', default=os.environ.get('EV_RUN_ID') or utc_run_id())
    args = parser.parse_args()
    run_dir = run_directory(args.output_root, args.run_id)
    if run_dir.exists():
        raise ValueError(f'Run directory already exists: {run_dir}')
    run_dir.mkdir(parents=True)
    bind_context(run_dir, args.raw, args.metadata)
    spark = (SparkSession.builder.master(os.environ.get('SPARK_MASTER', 'local[*]')).appName('EV-Analytics-Phase10')
             .config('spark.sql.shuffle.partitions', os.environ.get('SPARK_SHUFFLE_PARTITIONS', '32'))
             .config('spark.sql.ansi.enabled', 'true').config('spark.sql.session.timeZone', 'UTC').getOrCreate())
    spark.sparkContext.setLogLevel('WARN')
    report = {'status': 'failed', 'run_id': args.run_id, 'started_at_utc': datetime.now(timezone.utc).isoformat(), 'run_dir': str(run_dir)}
    try:
        processed_at = datetime.now(timezone.utc).isoformat()
        report['bronze'] = build_bronze(spark, args.raw.resolve(), args.metadata.resolve(), run_dir / 'bronze')
        report['silver'] = build_silver(spark, run_dir / 'bronze', args.metadata.resolve(), run_dir / 'silver', args.run_id, processed_at)
        report['gold'] = build_gold(spark, run_dir / 'silver', args.metadata.resolve(), run_dir / 'gold', args.run_id, args.run_id)
        artifacts = inventory(run_dir, ['run_context.json', 'bronze', 'silver', 'gold'])
        report['quality'] = verify_gold(spark, run_dir / 'gold', args.metadata.resolve())
        if inventory(run_dir, ['run_context.json', 'bronze', 'silver', 'gold']) != artifacts:
            raise RuntimeError('Artifacts changed during quality checks')
        marker = {'status': 'published', 'run_id': args.run_id, 'published_at_utc': datetime.now(timezone.utc).isoformat(), 'quality': report['quality']}
        marker['artifacts'] = artifacts
        (run_dir / 'published.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
        report['status'] = 'passed'
    finally:
        report['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        (run_dir / 'run_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        spark.stop()
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
