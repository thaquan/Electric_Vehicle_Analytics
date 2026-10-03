from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator

ROOT = Path(os.environ.get('EV_PROJECT_ROOT', Path(__file__).resolve().parents[1]))
PYTHON = os.environ.get('EV_PYTHON', sys.executable)


def failure_alert(context):
    ti = context.get('task_instance')
    logging.error(
        'EV Phase 10 task failed: dag_id=%s task_id=%s run_id=%s try=%s',
        getattr(ti, 'dag_id', None),
        getattr(ti, 'task_id', None),
        context.get('run_id'),
        getattr(ti, 'try_number', None),
    )


def stage_command(stage: str) -> str:
    return (
        f'cd "{ROOT}" && '
        f'"{PYTHON}" -m src.stage_runner {stage} '
        '--run-id "{{ dag_run.conf.get(\'run_id\') or ts_nodash }}"'
    )


default_args = {
    'owner': 'ev-analytics',
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
    'on_failure_callback': failure_alert,
}

with DAG(
    dag_id='ev_analytics_phase10',
    description='Standalone EV analytics: input check -> Bronze -> Silver -> Gold -> quality -> publish',
    default_args=default_args,
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=['ev-analytics', 'phase10', 'pyspark'],
) as dag:
    input_check = BashOperator(task_id='input_check', bash_command=stage_command('input_check'))
    bronze = BashOperator(task_id='bronze', bash_command=stage_command('bronze'))
    silver = BashOperator(task_id='silver', bash_command=stage_command('silver'))
    gold = BashOperator(task_id='gold', bash_command=stage_command('gold'))
    quality = BashOperator(task_id='quality', bash_command=stage_command('quality'))
    publish = BashOperator(task_id='publish', bash_command=stage_command('publish'))

    input_check >> bronze >> silver >> gold >> quality >> publish
