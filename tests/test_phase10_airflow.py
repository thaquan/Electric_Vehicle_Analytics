"""Run in the Airflow Linux image to exercise its actual template renderer."""
import importlib.util
import os
import json
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

from pipeline_fixture import create_fixture


def load_dag():
    path = Path(__file__).resolve().parents[1] / 'dags/ev_analytics_phase10.py'
    spec = importlib.util.spec_from_file_location('review_airflow_dag', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.dag


@unittest.skipUnless(sys.platform == 'linux' and importlib.util.find_spec('airflow'), 'Requires Airflow on Linux')
class AirflowTemplateTests(unittest.TestCase):
    def test_conf_cannot_execute_shell_substitution(self):
        with tempfile.TemporaryDirectory() as temporary:
            sentinel = Path(temporary) / 'must_not_exist'
            malicious_id = f'$(touch {sentinel})'
            task = load_dag().get_task('input_check')
            task.render_template_fields({'dag_run': SimpleNamespace(conf={'run_id': malicious_id}, id=7),
                                         'ts_nodash': '20261003T000000'})
            self.assertEqual(task.env['EV_RUN_ID'], malicious_id)
            result = subprocess.run(task.bash_command, shell=True, executable='/bin/bash',
                                    env={**os.environ, **task.env}, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('run_id must be', result.stderr)
            self.assertFalse(sentinel.exists())

    def fixture_dag(self, root):
        dag = load_dag()
        raw, meta = create_fixture(root)
        for task in dag.tasks:
            task.retries = 0
            task.execution_timeout = timedelta(minutes=10)
            task.bash_command += (f' --raw {shlex.quote(str(raw))}'
                                  f' --metadata {shlex.quote(str(meta))}'
                                  f' --output-root {shlex.quote(str(root / "output"))}')
        return dag, raw

    def test_real_dag_executes_all_stages_and_publishes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dag, _ = self.fixture_dag(root)
            run = dag.test(execution_date=datetime(2026, 1, 2, tzinfo=timezone.utc),
                           run_conf={'run_id': 'airflow_fixture'})
            self.assertEqual(run.state, 'success')
            states = {ti.task_id: ti.state for ti in run.get_task_instances()}
            self.assertEqual(states, {name: 'success' for name in ('input_check', 'bronze', 'silver', 'gold', 'quality', 'publish')})
            folder = root / 'output/runs/airflow_fixture'
            self.assertEqual(json.loads((folder / 'published.json').read_text())['status'], 'published')
            self.assertEqual(json.loads((folder / 'quality_report.json').read_text())['silver_reconstruction'], 'exact')

    def test_invalid_source_blocks_downstream_and_publish(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dag, raw = self.fixture_dag(root)
            with (raw / 'train.csv').open('a') as stream:
                stream.write('corrupt\n')
            run = dag.test(execution_date=datetime(2026, 1, 3, tzinfo=timezone.utc),
                           run_conf={'run_id': 'airflow_rejected'})
            self.assertEqual(run.state, 'failed')
            states = {ti.task_id: ti.state for ti in run.get_task_instances()}
            self.assertEqual(states.pop('input_check'), 'failed')
            self.assertTrue(states)
            self.assertEqual(set(states.values()), {'upstream_failed'})
            folder = root / 'output/runs/airflow_rejected'
            self.assertFalse((folder / 'published.json').exists())
            self.assertFalse((folder / 'bronze').exists())
