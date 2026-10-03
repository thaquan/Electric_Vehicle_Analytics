import ast
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.run_contract import run_directory, bind_context, write_json
from src.stage_runner import completed, run_stage, stage_inventory, write_marker
from src.quality_checks import check_aggregate_rows, verify_gold

ROOT = Path(__file__).resolve().parents[1]


class Phase10OrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.raw, self.meta = self.root / 'raw', self.root / 'meta'
        self.raw.mkdir(); self.meta.mkdir()
        (self.raw / 'train.csv').write_text('id\n1\n')
        (self.meta / 'source_manifest.json').write_text('{}')
        self.run = run_directory(self.root, 'test_run')
        self.run.mkdir(parents=True)
        bind_context(self.run, self.raw, self.meta)

    def seal(self, stage):
        write_marker(self.run, stage, {'status': 'passed', 'stage': stage, 'run_id': self.run.name,
                                      'artifacts': stage_inventory(self.run, stage)})

    def seed_gold(self):
        (self.run / 'input_check_report.json').write_text('{}')
        self.seal('input_check')
        for stage in ('bronze', 'silver', 'gold'):
            (self.run / stage).mkdir()
            (self.run / stage / 'part.parquet').write_bytes(b'fixture')
            self.seal(stage)

    def test_dag_has_required_tasks_and_safe_environment(self):
        text = (ROOT / 'dags/ev_analytics_phase10.py').read_text()
        tree = ast.parse(text)
        task_ids = {kw.value.value for node in ast.walk(tree) if isinstance(node, ast.Call)
                    for kw in node.keywords if kw.arg == 'task_id' and isinstance(kw.value, ast.Constant)}
        self.assertEqual(task_ids, {'input_check', 'bronze', 'silver', 'gold', 'quality', 'publish'})
        self.assertIn('input_check>>bronze>>silver>>gold>>quality>>publish', ''.join(text.split()))
        # Load only the command builder: Airflow need not be installed in unit tests.
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'stage_command')
        import shlex
        namespace = {'ROOT': ROOT, 'PYTHON': '/python path/python', 'shlex': shlex}
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<dag>', 'exec'), namespace)
        command = namespace['stage_command']('bronze')
        self.assertIn('--run-id "$EV_RUN_ID"', command)
        self.assertNotIn('{{', command)
        self.assertIn("'append_env': True", text)

    def test_invalid_run_ids_rejected_before_filesystem_writes(self):
        for value in ('../escape', '/tmp/escape', 'a/b', r'a\b', 'a b', '$(touch pwned)', 'x";echo hi', '', 'CON', 'a'*129):
            with self.subTest(value=value), self.assertRaises(ValueError):
                run_stage('bronze', value, self.raw, self.meta, self.root)

    def test_retry_missing_artifacts_rejected(self):
        (self.run / 'input_check_report.json').write_text('{}')
        write_marker(self.run, 'bronze', {'status': 'passed', 'stage': 'bronze', 'run_id': 'test_run'})
        with self.assertRaisesRegex(RuntimeError, 'unsealed'):
            run_stage('bronze', 'test_run', self.raw, self.meta, self.root)

    def test_retry_changed_or_missing_data_rejected(self):
        self.seed_gold()
        target = self.run / 'bronze/part.parquet'
        target.write_bytes(b'changed')
        with self.assertRaises(RuntimeError):
            run_stage('bronze', 'test_run', self.raw, self.meta, self.root)
        target.unlink()
        with self.assertRaises(RuntimeError):
            completed(self.run, 'bronze')

    def test_retry_unchanged_data_skips_spark(self):
        self.seed_gold()
        with patch('src.stage_runner.spark_session') as spark:
            self.assertEqual(run_stage('bronze', 'test_run', self.raw, self.meta, self.root)['status'], 'passed')
            spark.assert_not_called()

    def test_changed_input_or_configuration_rejected(self):
        for path in (self.raw / 'train.csv', self.meta / 'source_manifest.json'):
            original = path.read_bytes(); path.write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError, 'changed'):
                bind_context(self.run, self.raw, self.meta)
            path.write_bytes(original)

    def test_publish_without_quality_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Required stage'):
            run_stage('publish', 'test_run', self.raw, self.meta, self.root)
        self.assertFalse((self.run / 'published.json').exists())

    def test_quality_failure_does_not_publish(self):
        self.seed_gold()
        with patch('src.stage_runner.spark_session', return_value=Mock()), patch('src.stage_runner.verify_gold', side_effect=ValueError('bad KPI')):
            with self.assertRaisesRegex(ValueError, 'bad KPI'):
                run_stage('quality', 'test_run', self.raw, self.meta, self.root)
        self.assertFalse((self.run / 'published.json').exists())
        with self.assertRaises(RuntimeError):
            run_stage('publish', 'test_run', self.raw, self.meta, self.root)

    def test_publish_binds_quality_to_unchanged_gold(self):
        self.seed_gold()
        write_json(self.run / 'quality_report.json', {'status': 'passed'})
        self.seal('quality')
        (self.run / 'gold/part.parquet').write_bytes(b'tampered')
        with self.assertRaises(RuntimeError):
            run_stage('publish', 'test_run', self.raw, self.meta, self.root)
        self.assertFalse((self.run / 'published.json').exists())

    def test_valid_publish_and_retry(self):
        self.seed_gold()
        write_json(self.run / 'quality_report.json', {'status': 'passed'})
        self.seal('quality')
        result = run_stage('publish', 'test_run', self.raw, self.meta, self.root)
        self.assertEqual(result['result']['status'], 'published')
        self.assertTrue(completed(self.run, 'publish'))
        (self.run / 'published.json').unlink()
        with self.assertRaises(RuntimeError):
            run_stage('publish', 'test_run', self.raw, self.meta, self.root)

    def test_missing_kpi_rejected_before_spark_read(self):
        for name in ('gold_expected_metrics', 'star_expected_metrics', 'gold_spec'):
            (self.meta / (name + '.json')).write_text('{}')
        gold = self.run / 'gold'; gold.mkdir()
        from star_schema import DIMENSIONS
        for role in ['fact_ev_purchase_intent', *[d['role'] for d in DIMENSIONS], 'agg_ev_segments']:
            (gold / (role + '.parquet')).write_bytes(b'fixture')
        spark = Mock()
        with self.assertRaisesRegex(ValueError, 'eight'):
            verify_gold(spark, gold, self.meta)
        spark.read.parquet.assert_not_called()

    def test_aggregate_duplicate_missing_counts_and_rates_rejected(self):
        row = {'source_dataset': 'train', 'respondent_count': 10, 'yes_count': 2, 'no_count': 8, 'purchase_intent_rate': 0.2}
        wanted = {('train',): (10, 2)}
        check_aggregate_rows([row], wanted, ('source_dataset',))
        for rows in ([], [row, row], [{**row, 'no_count': 7}], [{**row, 'purchase_intent_rate': 0.3}],
                     [{**row, 'purchase_intent_rate': float('nan')}], [{**row, 'source_dataset': None}]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                check_aggregate_rows(rows, wanted, ('source_dataset',))


if __name__ == '__main__':
    unittest.main()
