import ast
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Phase10OrchestrationTests(unittest.TestCase):
    def test_dag_has_required_tasks_and_dependency_chain(self):
        text = (ROOT / 'dags' / 'ev_analytics_phase10.py').read_text(encoding='utf-8')
        tree = ast.parse(text)
        task_ids = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == 'task_id' and isinstance(kw.value, ast.Constant):
                        task_ids.add(kw.value.value)
        self.assertEqual(task_ids, {'input_check', 'bronze', 'silver', 'gold', 'quality', 'publish'})
        normalized = ''.join(text.split())
        self.assertIn('input_check>>bronze>>silver>>gold>>quality>>publish', normalized)
        self.assertIn("'retries':2", normalized)
        self.assertIn('on_failure_callback', text)

    def test_publish_is_guarded_by_quality_marker(self):
        text = (ROOT / 'src' / 'stage_runner.py').read_text(encoding='utf-8')
        normalized = ''.join(text.split())
        self.assertIn("require_stage(run_dir,'quality')", normalized)
        self.assertIn("quality.get('status')!='passed'", normalized)
        self.assertIn("raiseRuntimeError('Qualityreportisnotpassed;refusingpublish')", normalized)

    def test_completed_stage_short_circuits_retry(self):
        text = (ROOT / 'src' / 'stage_runner.py').read_text(encoding='utf-8')
        normalized = ''.join(text.split())
        self.assertIn("ifcompleted(run_dir,stage):", normalized)
        self.assertIn("'status':'already_passed'", normalized)


if __name__ == '__main__':
    unittest.main()
