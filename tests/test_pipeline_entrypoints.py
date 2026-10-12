"""Regression checks for shared validation, lifecycle failures and runtime ownership."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.run_pipeline import execute_pipeline
from src.stage_runner import run_stage
from src.runtime import cached_frames


class EntrypointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.raw, self.meta = self.root / 'raw', self.root / 'metadata'
        self.raw.mkdir(); self.meta.mkdir()
        data = b'id,Age,Will_Buy_EV\n1,30,Maybe\n'
        (self.raw / 'train.csv').write_bytes(data)
        self.write(self.meta / 'source_manifest.json', {'files': [{
            'name': 'train.csv', 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest().upper(),
            'columns': ['id', 'Age', 'Will_Buy_EV'], 'data_rows': 1}]})
        self.write(self.meta / 'categorical_profile.json', {'train.csv': [
            {'name': 'Will_Buy_EV', 'value_counts': {'Yes': 1, 'No': 0}}]})
        self.write(self.meta / 'profiling_summary.json', [{'file': 'train.csv', 'column_profiles': [
            {'name': 'id', 'min': 1, 'max': 1}, {'name': 'Age', 'min': 30, 'max': 30},
            {'name': 'Will_Buy_EV'}]}])

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def valid_input(self, raw, meta, report):
        self.write(report, {'status': 'passed'})

    def run_path(self, output='out'):
        return self.root / output / 'runs/run'

    def test_invalid_category_stops_all_entrypoints_before_spark(self):
        for name in ('cli', 'stage', 'databricks'):
            with self.subTest(name=name):
                factory = Mock(side_effect=AssertionError('Spark must not start'))
                with self.assertRaisesRegex(ValueError, 'category|Yes/No'):
                    if name == 'stage':
                        run_stage('input_check', 'run', self.raw, self.meta, self.root / name,
                                  session_factory=factory)
                    else:
                        execute_pipeline(self.raw, self.meta, self.root / name, 'run',
                            runtime='databricks-serverless' if name == 'databricks' else 'local',
                            session_factory=factory)
                factory.assert_not_called()
                folder = self.run_path(name)
                self.assertFalse((folder / 'published.json').exists())
                self.assertEqual(json.loads((folder / 'input_check_report.json').read_text())['status'], 'failed')
                if name != 'stage':
                    report = json.loads((folder / 'run_report.json').read_text())
                    self.assertEqual(report['failed_stage'], 'input_check')

    def test_missing_inputs_still_produce_run_failure_report(self):
        factory = Mock()
        with self.assertRaisesRegex(RuntimeError, 'Missing raw'):
            execute_pipeline(self.root / 'missing', self.meta, self.root / 'out', 'run',
                             session_factory=factory)
        factory.assert_not_called()
        self.assertEqual(json.loads((self.run_path() / 'run_report.json').read_text())['status'], 'failed')

    def test_spark_startup_failure_is_reported_and_not_published(self):
        factory = Mock(side_effect=RuntimeError('JVM unavailable'))
        with patch('src.stage_runner.prepare', side_effect=self.valid_input):
            with self.assertRaisesRegex(RuntimeError, 'JVM unavailable'):
                execute_pipeline(self.raw, self.meta, self.root / 'out', 'run', session_factory=factory)
        report = json.loads((self.run_path() / 'run_report.json').read_text())
        self.assertEqual(report['failed_stage'], 'bronze')
        self.assertEqual(report['error'], 'JVM unavailable')
        self.assertEqual(json.loads((self.run_path() / 'stage_status/bronze.json').read_text())['status'], 'failed')
        self.assertFalse((self.run_path() / 'published.json').exists())

    def test_processing_error_survives_session_cleanup_error(self):
        session = Mock()
        session.stop.side_effect = RuntimeError('stop failed')
        with patch('src.stage_runner.prepare', side_effect=self.valid_input), \
             patch('src.stage_runner.build_bronze', side_effect=ValueError('bad source')):
            with self.assertRaisesRegex(ValueError, 'bad source'):
                execute_pipeline(self.raw, self.meta, self.root / 'out', 'run',
                                 session_factory=lambda stage: session)
        report = json.loads((self.run_path() / 'run_report.json').read_text())
        self.assertEqual(report['error'], 'bad source')
        self.assertIn('stop failed', ' '.join(report['notes']))
        session.stop.assert_called_once()

    def test_failed_report_write_does_not_replace_original_error(self):
        with patch('src.run_pipeline.write_json', side_effect=OSError('report unavailable')):
            with self.assertRaisesRegex(ValueError, 'Yes/No') as caught:
                execute_pipeline(self.raw, self.meta, self.root / 'out', 'run')
        self.assertIn('report unavailable', ' '.join(caught.exception.__notes__))

    def test_existing_run_is_untouched(self):
        self.write(self.run_path() / 'run_report.json', {'preserve': True})
        with self.assertRaises(FileExistsError):
            execute_pipeline(self.raw, self.meta, self.root / 'out', 'run')
        self.assertEqual(json.loads((self.run_path() / 'run_report.json').read_text()), {'preserve': True})

    def test_serverless_pipeline_uses_shared_gates_without_stopping_platform(self):
        session = Mock()
        def build(spark, source, metadata, target, *args, **kwargs):
            self.assertIs(spark, session)
            target.mkdir()
            (target / 'part.parquet').write_bytes(b'fixture')
            return {'status': 'passed'}
        with patch('src.stage_runner.prepare', side_effect=self.valid_input), \
             patch('src.stage_runner.build_bronze', side_effect=build), \
             patch('src.stage_runner.build_silver', side_effect=build), \
             patch('src.stage_runner.build_gold', side_effect=build) as gold, \
             patch('src.stage_runner.verify_gold', return_value={'status': 'passed'}) as quality:
            report = execute_pipeline(self.raw, self.meta, self.root / 'out', 'run',
                runtime='databricks-serverless', session_factory=lambda stage: session)
        self.assertEqual(report['status'], 'passed')
        self.assertFalse(gold.call_args.kwargs['cache_enabled'])
        self.assertFalse(quality.call_args.kwargs['cache_enabled'])
        session.stop.assert_not_called()
        marker = json.loads((self.run_path() / 'published.json').read_text())
        self.assertIn('input_check_report.json', marker['artifacts'])
        self.assertIn('gold/part.parquet', marker['artifacts'])
        with self.assertRaisesRegex(RuntimeError, 'changed'):
            run_stage('publish', 'run', self.raw, self.meta, self.root / 'out')

    def test_cache_disabled_never_calls_platform_cache_methods(self):
        frame = Mock()
        with cached_frames(False) as keep:
            self.assertIs(keep(frame), frame)
        frame.cache.assert_not_called()
        frame.unpersist.assert_not_called()

    def test_cache_cleanup_attempts_all_frames_and_preserves_original(self):
        first, second = Mock(), Mock()
        first.cache.return_value = first; second.cache.return_value = second
        second.unpersist.side_effect = RuntimeError('unpersist failed')
        with self.assertRaisesRegex(ValueError, 'invalid table') as caught:
            with cached_frames() as keep:
                keep(first); keep(second)
                raise ValueError('invalid table')
        first.unpersist.assert_called_once(); second.unpersist.assert_called_once()
        self.assertIn('unpersist failed', ' '.join(caught.exception.__notes__))


if __name__ == '__main__':
    unittest.main()
