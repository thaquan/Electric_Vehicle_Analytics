"""Run in the Airflow Linux image to exercise its actual template renderer."""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


@unittest.skipUnless(sys.platform == 'linux' and importlib.util.find_spec('airflow'), 'Requires Airflow on Linux')
class AirflowTemplateTests(unittest.TestCase):
    def test_conf_cannot_execute_shell_substitution(self):
        path = Path(__file__).resolve().parents[1] / 'dags/ev_analytics_phase10.py'
        spec = importlib.util.spec_from_file_location('review_airflow_dag', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temporary:
            sentinel = Path(temporary) / 'must_not_exist'
            malicious_id = f'$(touch {sentinel})'
            task = module.dag.get_task('input_check')
            task.render_template_fields({'dag_run': SimpleNamespace(conf={'run_id': malicious_id}, id=7),
                                         'ts_nodash': '20261003T000000'})
            self.assertEqual(task.env['EV_RUN_ID'], malicious_id)
            result = subprocess.run(task.bash_command, shell=True, executable='/bin/bash',
                                    env={**os.environ, **task.env}, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('run_id must be', result.stderr)
            self.assertFalse(sentinel.exists())
