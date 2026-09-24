import copy
import ast
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from pipeline_contract import check_pipeline_id, check_run_id, require_publication
from gold_rules import require_gold_context

PIPELINE_ID = "12345678-1234-1234-1234-123456789012"


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.silver = json.loads((ROOT / "metadata/silver_published_run.json").read_text())
        self.gold = json.loads((ROOT / "metadata/gold_published_run.json").read_text())

    def test_manual_historical_publications_valid(self):
        require_publication(self.silver, "silver", self.silver["run_id"])
        require_publication(self.gold, "gold", self.gold["run_id"], silver_run_id=self.silver["run_id"])

    def test_old_run_not_accepted_in_new_pipeline(self):
        with self.assertRaises(ValueError):
            require_publication(self.silver, "silver", self.silver["run_id"], PIPELINE_ID)
        self.silver["pipeline_run_id"] = PIPELINE_ID
        require_publication(self.silver, "silver", self.silver["run_id"], PIPELINE_ID)

    def test_partial_or_wrong_tables_fail(self):
        for mutation in ("missing", "duplicate", "count", "name", "status"):
            marker = copy.deepcopy(self.silver)
            if mutation == "missing": marker["tables"].pop()
            if mutation == "duplicate": marker["tables"].append(marker["tables"][0])
            if mutation == "count": marker["tables"][0]["rows"] -= 1
            if mutation == "name": marker["tables"][0]["table"] = "other_run"
            if mutation == "status": marker["status"] = "failed"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                require_publication(marker, "silver", marker["run_id"])

    def test_gold_wrong_parent_rejected(self):
        with self.assertRaises(ValueError):
            require_publication(self.gold, "gold", self.gold["run_id"], silver_run_id="20260924T000000000000Z")

    def test_missing_injection_and_unsafe_run_ids_fail(self):
        with self.assertRaises(ValueError): check_pipeline_id("", required=True)
        with self.assertRaises(ValueError): check_pipeline_id("../other")
        for value in ("", "../other", "20260924", None):
            with self.assertRaises(ValueError): check_run_id(value)

    def test_notebook_verifies_injected_run_not_historical_default(self):
        # Execute the actual orchestration branch; Spark I/O is mocked, not claimed tested.
        config = json.loads((ROOT / "metadata/fabric_workspace.json").read_text())
        spec = json.loads((ROOT / "metadata/gold_spec.json").read_text())
        expected = json.loads((ROOT / "metadata/gold_expected_metrics.json").read_text())
        new_run = "20260925T123456123456Z"
        marker = copy.deepcopy(self.silver)
        old_run = marker["run_id"]
        marker["run_id"], marker["pipeline_run_id"] = new_run, PIPELINE_ID
        for table in marker["tables"]:
            table["table"] = table["table"].replace(old_run.lower(), new_run.lower())
        utils = types.ModuleType("notebookutils")
        utils.runtime = types.SimpleNamespace(context={"isForPipeline": True, "defaultLakehouseId": config["gold_lakehouse_id"], "defaultLakehouseWorkspaceId": config["workspace_id"]})
        utils.fs = types.SimpleNamespace(head=MagicMock(return_value=json.dumps(marker)))
        sql = types.ModuleType("pyspark.sql")
        sql.SparkSession, sql.functions = MagicMock(), MagicMock()
        verification = MagicMock()
        scope = dict(CONFIG=config, DEFAULT_SPEC=spec, EXPECTED=expected, pipeline_run_id=PIPELINE_ID,
                     silver_run_id=new_run, run_mode="verify_silver", check_pipeline_id=check_pipeline_id,
                     check_run_id=check_run_id, require_gold_context=require_gold_context,
                     require_publication=require_publication, verify_published_tables=verification)
        tree = ast.parse((ROOT / "scripts/fabric_gold.py").read_text())
        function = ast.Module(body=[tree.body[0]], type_ignores=[])
        with patch.dict(sys.modules, {"notebookutils": utils, "pyspark": types.ModuleType("pyspark"), "pyspark.sql": sql}):
            exec(compile(function, "fabric_gold.py", "exec"), scope)
            result = scope["execute_gold"]("")
        self.assertEqual(result["run_id"], new_run)
        self.assertEqual(result["status"], "verified")
        self.assertIn(new_run + "_published.json", utils.fs.head.call_args.args[0])
        self.assertEqual(verification.call_args.args[2]["pipeline_run_id"], PIPELINE_ID)

    def test_pipeline_wiring_and_notebook_parameters(self):
        payload = json.loads((ROOT / "PL_EV_E2E.DataPipeline/pipeline-content.json").read_text())
        activities = payload["properties"]["activities"]
        self.assertEqual([a["name"] for a in activities], ["Check_Bronze", "Build_Silver", "Validate_Silver", "Build_Gold", "Validate_Gold"])
        for i, activity in enumerate(activities):
            self.assertEqual(activity["policy"]["retry"], 0)
            self.assertEqual(activity["dependsOn"], [] if i == 0 else [{"activity": activities[i-1]["name"], "dependencyConditions": ["Succeeded"]}])
            parameters = activity["typeProperties"]["parameters"]
            self.assertEqual(parameters["pipeline_run_id"]["value"]["value"], "@pipeline().RunId")
            if i >= 2:
                self.assertEqual(parameters["silver_run_id"]["value"]["value"], "@json(activity('Build_Silver').output.result.exitValue).run_id")
        self.assertEqual(activities[-1]["typeProperties"]["parameters"]["gold_run_id"]["value"]["value"], "@json(activity('Build_Gold').output.result.exitValue).run_id")
        for name in ("NB_EV_Bronze_To_Silver", "NB_EV_Silver_To_Gold"):
            notebook = json.loads((ROOT / f"notebooks/{name}.ipynb").read_text())
            parameter_cells = [c for c in notebook["cells"] if "parameters" in c["metadata"].get("tags", [])]
            self.assertEqual(len(parameter_cells), 1)
            self.assertIs(parameter_cells[0], notebook["cells"][0])
            self.assertIn("notebookutils.notebook.exit", "".join(notebook["cells"][-1]["source"]))
            source = (ROOT / f"{name}.Notebook/notebook-content.py").read_text()
            self.assertEqual(source.count("# PARAMETERS CELL"), 1)
            compile(source, name, "exec")


if __name__ == "__main__":
    unittest.main()
