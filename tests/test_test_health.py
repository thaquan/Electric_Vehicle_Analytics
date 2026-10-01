import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_test_health import check


class HealthCheckTests(unittest.TestCase):
    def run_check(self, report_model="a97a9cc1-eaac-4007-b8ad-c146ac1776c5",
                  refresh_status="Completed", respondents=668665):
        responses = [
            {"datasetId": report_model, "datasetWorkspaceId": "27873d0c-580a-4963-9e25-5846948f1c5d"},
            {"value": [{"status": refresh_status}]},
            {"results": [{"tables": [{"rows": [{"[respondents]": respondents, "[yes]": 116779, "[no]": 551886}]}]}]},
        ]
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "health.json"
            with patch("check_test_health.Client") as client, contextlib.redirect_stdout(io.StringIO()):
                client.return_value.request.side_effect = [(200, {}, json.dumps(r).encode()) for r in responses]
                try:
                    check(output)
                except ValueError:
                    pass
            return json.loads(output.read_text())

    def test_healthy_target_passes(self):
        self.assertEqual(self.run_check()["status"], "passed")

    def test_wrong_model_fails_before_kpi(self):
        result = self.run_check(report_model="source-model")
        self.assertEqual(result["status"], "failed")
        self.assertNotIn("actual_kpi", result)

    def test_failed_refresh_is_not_hidden_by_old_good_data(self):
        self.assertEqual(self.run_check(refresh_status="Failed")["status"], "failed")

    def test_kpi_drift_is_recorded_as_failure(self):
        result = self.run_check(respondents=1)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["actual_kpi"]["respondents"], 1)


if __name__ == "__main__":
    unittest.main()
