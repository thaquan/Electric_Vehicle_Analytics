from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from pyspark.sql import SparkSession

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.bronze_silver import prepare
from src.bronze import build_bronze
from src.silver import build_silver
from src.gold import build_gold
from src.quality_checks import verify_gold
from src.run_contract import run_directory, bind_context, inventory, write_json

STAGES = ('input_check', 'bronze', 'silver', 'gold', 'quality', 'publish')
ARTIFACTS = ('input_check_report.json', 'bronze', 'silver', 'gold', 'quality_report.json', 'published.json')


def stage_inventory(run_dir: Path, stage: str) -> dict:
    return inventory(run_dir, ['run_context.json', *ARTIFACTS[:STAGES.index(stage) + 1]])


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def marker_path(run_dir: Path, stage: str) -> Path:
    return run_dir / 'stage_status' / f'{stage}.json'


def read_marker(run_dir: Path, stage: str):
    path = marker_path(run_dir, stage)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def write_marker(run_dir: Path, stage: str, payload: dict) -> None:
    path = marker_path(run_dir, stage)
    write_json(path, payload)


def completed(run_dir: Path, stage: str) -> bool:
    marker = read_marker(run_dir, stage)
    if not marker or marker.get('status') != 'passed':
        return False
    if marker.get('stage') != stage or marker.get('run_id') != run_dir.name:
        raise RuntimeError('Stage marker identity mismatch; use a new run_id')
    if not marker.get('artifacts') or marker['artifacts'] != stage_inventory(run_dir, stage):
        raise RuntimeError('Stage artifacts missing, changed or unsealed; use a new run_id')
    return True


def require_stage(run_dir: Path, stage: str) -> None:
    if not completed(run_dir, stage):
        raise RuntimeError(f'Required stage not passed: {stage}')


def spark_session(stage: str) -> SparkSession:
    spark = (SparkSession.builder
             .master(os.environ.get('SPARK_MASTER', 'local[*]'))
             .appName(f'EV-Analytics-Phase10-{stage}')
             .config('spark.sql.ansi.enabled', 'true')
             .config('spark.sql.session.timeZone', 'UTC')
             .config('spark.sql.shuffle.partitions', os.environ.get('SPARK_SHUFFLE_PARTITIONS', '32'))
             .getOrCreate())
    spark.sparkContext.setLogLevel('WARN')
    return spark


def reset_dir(path: Path, run_dir: Path) -> None:
    if path.resolve() != path or not path.resolve().is_relative_to(run_dir.resolve()) or path == run_dir:
        raise ValueError('Refusing to reset a directory outside this run')
    if path.exists():
        # Inspect descendants before recursive deletion, including junctions.
        for child in path.rglob('*'):
            if child.is_symlink() or child.resolve() != child:
                raise ValueError('Refusing to reset a linked artifact')
        shutil.rmtree(path)


def run_stage(stage: str, run_id: str, raw: Path, metadata: Path, output_root: Path) -> dict:
    if stage not in STAGES:
        raise ValueError(f'Unknown stage: {stage}')
    run_dir = run_directory(output_root, run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    bind_context(run_dir, raw, metadata)

    if completed(run_dir, stage):
        marker = read_marker(run_dir, stage)
        print(json.dumps({'status': 'already_passed', 'stage': stage, 'run_id': run_id, 'marker': marker}, indent=2))
        return marker

    started = utc_now()
    result = None
    try:
        if stage == 'input_check':
            report_path = run_dir / 'input_check_report.json'
            prepare(raw.resolve(), metadata.resolve(), report_path)
            result = json.loads(report_path.read_text(encoding='utf-8'))

        elif stage == 'bronze':
            require_stage(run_dir, 'input_check')
            target = run_dir / 'bronze'
            reset_dir(target, run_dir)
            spark = spark_session(stage)
            try:
                result = build_bronze(spark, raw.resolve(), metadata.resolve(), target)
            finally:
                spark.stop()

        elif stage == 'silver':
            require_stage(run_dir, 'bronze')
            target = run_dir / 'silver'
            reset_dir(target, run_dir)
            spark = spark_session(stage)
            try:
                result = build_silver(spark, run_dir / 'bronze', metadata.resolve(), target, run_id, utc_now())
            finally:
                spark.stop()

        elif stage == 'gold':
            require_stage(run_dir, 'silver')
            target = run_dir / 'gold'
            reset_dir(target, run_dir)
            spark = spark_session(stage)
            try:
                result = build_gold(spark, run_dir / 'silver', metadata.resolve(), target, run_id, run_id)
            finally:
                spark.stop()

        elif stage == 'quality':
            require_stage(run_dir, 'gold')
            before = stage_inventory(run_dir, 'gold')
            spark = spark_session(stage)
            try:
                result = verify_gold(spark, run_dir / 'gold', metadata.resolve())
            finally:
                spark.stop()
            if before != stage_inventory(run_dir, 'gold'):
                raise RuntimeError('Artifacts changed during quality checks')
            (run_dir / 'quality_report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')

        else:
            require_stage(run_dir, 'quality')
            quality = json.loads((run_dir / 'quality_report.json').read_text(encoding='utf-8'))
            if quality.get('status') != 'passed':
                raise RuntimeError('Quality report is not passed; refusing publish')
            result = {'status': 'published', 'run_id': run_id, 'published_at_utc': utc_now(), 'quality': quality}
            (run_dir / 'published.json').write_text(json.dumps(result, indent=2), encoding='utf-8')

        payload = {'status': 'passed', 'stage': stage, 'run_id': run_id, 'started_at_utc': started, 'finished_at_utc': utc_now(), 'result': result}
        payload['artifacts'] = stage_inventory(run_dir, stage)
        write_marker(run_dir, stage, payload)
        print(json.dumps(payload, indent=2))
        return payload
    except Exception as exc:
        payload = {'status': 'failed', 'stage': stage, 'run_id': run_id, 'started_at_utc': started, 'finished_at_utc': utc_now(), 'error': str(exc)}
        write_marker(run_dir, stage, payload)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=STAGES)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--raw', type=Path, default=ROOT / 'data/raw/kaggle')
    parser.add_argument('--metadata', type=Path, default=ROOT / 'metadata')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'output/phase10')
    args = parser.parse_args()
    run_stage(args.stage, args.run_id, args.raw, args.metadata, args.output_root)


if __name__ == '__main__':
    main()
