from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from src.run_contract import run_directory, write_json
from src.stage_runner import STAGES, run_stage, utc_now
from src.runtime import cleanup

ROOT = Path(__file__).resolve().parents[1]


def utc_run_id():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')


def execute_pipeline(raw: Path, metadata: Path, output_root: Path, run_id: str,
                     *, runtime='local', session_factory=None):
    """Use the same validation, stage gates and publication as the Airflow CLI."""
    run_dir = run_directory(output_root, run_id)
    # Never replace an existing report or a sealed run.
    run_dir.mkdir(parents=True, exist_ok=False)
    report = {'status': 'failed', 'run_id': run_id, 'platform': runtime,
              'started_at_utc': utc_now(), 'run_dir': str(run_dir)}
    stage = 'input_check'
    try:
        for stage in STAGES:
            marker = run_stage(stage, run_id, raw, metadata, output_root,
                               runtime=runtime, session_factory=session_factory)
            report[stage] = marker['result']
        report['status'] = 'passed'
    except Exception as exc:
        report.update(failed_stage=stage, error=str(exc), error_type=type(exc).__name__,
                      notes=getattr(exc, '__notes__', []))
        raise
    finally:
        report['finished_at_utc'] = utc_now()
        cleanup([lambda: write_json(run_dir / 'run_report.json', report)])
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, default=ROOT / 'data/raw/kaggle')
    parser.add_argument('--metadata', type=Path, default=ROOT / 'metadata')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'output/phase10')
    parser.add_argument('--run-id', default=os.environ.get('EV_RUN_ID') or utc_run_id())
    args = parser.parse_args()
    print(json.dumps(execute_pipeline(args.raw, args.metadata, args.output_root, args.run_id), indent=2))


if __name__ == '__main__':
    main()
