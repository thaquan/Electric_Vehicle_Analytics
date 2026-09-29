"""Offline preparation checks. These tests never create Fabric resources."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
from prepare_recovery import prepare_model, prepare_report
from recovery_common import SOURCE_WORKSPACE, SOURCE_LAKEHOUSE, SOURCE_MODEL, read_json, validate_config, validate_context
from fabric_restore_gold import restore
from create_recovery_item import check_operation_url, operation_url_from_headers, check_payload
from verify_recovery_package import digest, verify_entries


def sample_config():
    config = read_json(PROJECT / "config/recovery.example.json")
    config.update(workspace_id="11111111-1111-4111-8111-111111111111",
                  lakehouse_id="22222222-2222-4222-8222-222222222222",
                  semantic_model_id="33333333-3333-4333-8333-333333333333")
    return config


def snapshot_path():
    bundled = PROJECT.parent / "snapshot"
    if bundled.exists():
        return bundled
    return PROJECT / "output/exports/gold_v2/20260925T152721965637Z/20260927T130004568586Z"


class RecoveryTests(unittest.TestCase):
    def test_placeholders_and_source_targets_rejected(self):
        with self.assertRaises(ValueError):
            validate_config(read_json(PROJECT / "config/recovery.example.json"))
        for key, source in [("workspace_id", SOURCE_WORKSPACE), ("lakehouse_id", SOURCE_LAKEHOUSE), ("semantic_model_id", SOURCE_MODEL)]:
            config = sample_config()
            config[key] = source.upper()
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_config(config, report=True)

    def test_unsafe_schema_rejected(self):
        config = sample_config()
        config["lakehouse_schema"] = "dbo; DROP TABLE x"
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_restore_rejects_wrong_context_before_spark_access(self):
        config = sample_config()
        context = {"currentWorkspaceId": config["workspace_id"], "defaultLakehouseWorkspaceId": config["workspace_id"],
                   "defaultLakehouseId": SOURCE_LAKEHOUSE}
        with self.assertRaisesRegex(ValueError, "defaultLakehouseId"):
            restore(None, context, config, execute=True)
        context["defaultLakehouseId"] = config["lakehouse_id"]
        validate_context(context, config)

    def test_prepare_model_rebinds_all_six_partitions_and_removes_source_id(self):
        config = sample_config()
        original = (PROJECT / "SM_EV_Analytics.SemanticModel/definition/expressions.tmdl").read_bytes()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "model"
            folder = prepare_model(PROJECT, snapshot_path(), config, output)
            text = "\n".join(p.read_text(encoding="utf-8") for p in folder.rglob("*.tmdl"))
            self.assertNotIn(SOURCE_WORKSPACE, text)
            self.assertNotIn(SOURCE_LAKEHOUSE, text)
            self.assertNotIn(SOURCE_MODEL, text)
            self.assertEqual(text.count("schemaName: dbo"), 6)
            self.assertEqual(text.count("mode: directLake"), 6)
            self.assertEqual(text.count("\tmeasure "), 12)
            sql = (output / "recovery_gold_checks.sql").read_text()
            self.assertNotIn("LH_EV_Silver", sql)
            self.assertEqual(read_json(output / "prepared.json")["status"], "prepared_not_deployed")
            check_payload("model", read_json(output / "create_semantic_model.json"), config)
            with self.assertRaises(ValueError):
                prepare_model(PROJECT, snapshot_path(), config, output)
        self.assertEqual((PROJECT / "SM_EV_Analytics.SemanticModel/definition/expressions.tmdl").read_bytes(), original)

    def test_legacy_lakehouse_omits_schema(self):
        config = sample_config()
        config["lakehouse_schema"] = ""
        with tempfile.TemporaryDirectory() as temp:
            folder = prepare_model(PROJECT, snapshot_path(), config, Path(temp) / "legacy")
            self.assertTrue(all("schemaName:" not in p.read_text() for p in (folder / "definition/tables").glob("*.tmdl")))

    def test_report_keeps_visuals_but_uses_new_model_and_identity(self):
        config = sample_config()
        with tempfile.TemporaryDirectory() as temp:
            folder = prepare_report(PROJECT, config, Path(temp) / "report")
            binding = (folder / "definition.pbir").read_text()
            self.assertIn(config["semantic_model_id"], binding)
            self.assertNotIn(SOURCE_MODEL, binding)
            payload = read_json(Path(temp) / "report/create_report.json")
            check_payload("report", payload, config)
            wrong_config = copy.deepcopy(config)
            wrong_config["semantic_model_id"] = "44444444-4444-4444-8444-444444444444"
            with self.assertRaises(ValueError):
                check_payload("report", payload, wrong_config)
            self.assertFalse((folder / ".pbi").exists())
            old = PROJECT / "RPT_EV_Analytics.Report"
            self.assertNotEqual(read_json(old / ".platform")["config"]["logicalId"], read_json(folder / ".platform")["config"]["logicalId"])
            visuals = list((old / "definition").rglob("visual.json"))
            self.assertEqual(len(visuals), 57)
            for visual in visuals:
                self.assertEqual(visual.read_bytes(), (folder / visual.relative_to(old)).read_bytes())

    def test_report_requires_new_model_id(self):
        config = sample_config()
        config["semantic_model_id"] = None
        with tempfile.TemporaryDirectory() as temp, self.assertRaises(ValueError):
            prepare_report(PROJECT, config, Path(temp) / "report")

    def test_package_rejects_corrupt_file_and_path_traversal(self):
        for relative in ["content.txt", "../content.txt"]:
            inventory = {"files": [{"path": relative, "bytes": 8, "sha256": digest(b"original")}]}
            raw = json.dumps(inventory).encode()
            data = {"package_manifest.json": raw, "package_manifest.sha256": (digest(raw) + "  package_manifest.json").encode(), relative: b"modified"}
            with self.subTest(path=relative), self.assertRaises(ValueError):
                verify_entries(data.__getitem__, list(data))

    def test_operation_polling_rejects_unrelated_hosts(self):
        self.assertEqual(check_operation_url("https://api.fabric.microsoft.com/v1/operations/123"),
                         "https://api.fabric.microsoft.com/v1/operations/123")
        for url in ["https://example.com/v1/operations/123", "http://api.fabric.microsoft.com/v1/operations/123",
                    "https://api.fabric.microsoft.com/v1/workspaces/123"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                check_operation_url(url)

    def test_regional_location_uses_public_endpoint_and_operation_id(self):
        operation_id = "d4999f5e-eaea-4aae-92c3-3f37638e1f96"
        headers = {"x-ms-operation-id": operation_id,
                   "Location": "https://wabi-south-east-asia-c-primary-redirect.analysis.windows.net/v1/operations/" + operation_id}
        self.assertEqual(operation_url_from_headers(headers),
                         "https://api.fabric.microsoft.com/v1/operations/" + operation_id)
        headers["x-ms-operation-id"] = "../workspaces/invalid"
        with self.assertRaises(ValueError):
            operation_url_from_headers(headers)
        self.assertEqual(operation_url_from_headers({"Location": "https://api.fabric.microsoft.com/v1/operations/123"}),
                         "https://api.fabric.microsoft.com/v1/operations/123")


if __name__ == "__main__":
    unittest.main()
