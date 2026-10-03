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

STAGES = ('input_check', 'bronze', 'silver', 'gold', 'quality', 'publish')


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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')


def completed(run_dir: Path, stage: str) -> bool:
    marker = read_marker(run_dir, stage)
    return bool(marker and marker.get('status') == 'passed')


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


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def run_stage(stage: str, run_id: str, raw: Path, metadata: Path, output_root: Path) -> dict:
    if stage not in STAGES:
        raise ValueError(f'Unknown stage: {stage}')
    run_dir = output_root / 'runs' / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

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
            reset_dir(target)
            spark = spark_session(stage)
            try:
                result = build_bronze(spark, raw.resolve(), metadata.resolve(), target)
            finally:
                spark.stop()

        elif stage == 'silver':
            require_stage(run_dir, 'bronze')
            target = run_dir / 'silver'
            reset_dir(target)
            spark = spark_session(stage)
            try:
                result = build_silver(spark, run_dir / 'bronze', metadata.resolve(), target, run_id, utc_now())
            finally:
                spark.stop()

        elif stage == 'gold':
            require_stage(run_dir, 'silver')
            target = run_dir / 'gold'
            reset_dir(target)
            spark = spark_session(stage)
            try:
                result = build_gold(spark, run_dir / 'silver', metadata.resolve(), target, run_id, run_id)
            finally:
                spark.stop()

        elif stage == 'quality':
            require_stage(run_dir, 'gold')
            spark = spark_session(stage)
            try:
                result = verify_gold(spark, run_dir / 'gold', metadata.resolve())
            finally:
                spark.stop()
            (run_dir / 'quality_report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')

        else:
            require_stage(run_dir, 'quality')
            quality = json.loads((run_dir / 'quality_report.json').read_text(encoding='utf-8'))
            if quality.get('status') != 'passed':
                raise RuntimeError('Quality report is not passed; refusing publish')
            result = {'status': 'published', 'run_id': run_id, 'published_at_utc': utc_now(), 'quality': quality}
            (run_dir / 'published.json').write_text(json.dumps(result, indent=2), encoding='utf-8')

        payload = {'status': 'passed', 'stage': stage, 'run_id': run_id, 'started_at_utc': started, 'finished_at_utc': utc_now(), 'result': result}
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
