"""Fail-closed checks for snapshot selection and portable export paths."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from export_gold_snapshot import inspect_log, safe_path, validate_audit, verify


class ExportGuardTests(unittest.TestCase):
    def setUp(self):
        self.table = {"rows": 1, "columns": [{"name": "id", "type": "bigint"}]}
        self.actions = [
            {"protocol": {"minReaderVersion": 1, "minWriterVersion": 2}},
            {"metaData": {"format": {"provider": "parquet"}, "partitionColumns": [],
                          "configuration": {}, "schemaString": json.dumps({"type": "struct", "fields": [
                              {"name": "id", "type": "long", "nullable": True, "metadata": {}}]})}},
            {"add": {"path": "part-00000.parquet", "size": 100,
                     "partitionValues": {}, "stats": json.dumps({"numRecords": 1})}},
        ]

    def inspect(self, actions):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "00000000000000000000.json"
            path.write_text("\n".join(json.dumps(a) for a in actions), encoding="utf-8")
            return inspect_log(path, self.table)

    def test_plain_unpartitioned_v0_is_accepted(self):
        self.assertEqual(len(self.inspect(self.actions)[2]), 1)

    def test_logical_delta_features_cannot_be_silently_copied(self):
        mutations = [
            lambda a: a[0]["protocol"].update(minReaderVersion=3),
            lambda a: a[1]["metaData"].update(partitionColumns=["id"]),
            lambda a: a[1]["metaData"]["configuration"].update({"delta.columnMapping.mode": "name"}),
            lambda a: a[2]["add"].update(deletionVector={"storageType": "i", "cardinality": 1}),
            lambda a: a.append({"remove": {"path": "part-00000.parquet"}}),
            lambda a: a.append(copy.deepcopy(a[2])),
            lambda a: a[2]["add"].update(path="../other.parquet"),
            lambda a: a[2]["add"].update(stats=json.dumps({"numRecords": 2})),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                actions = copy.deepcopy(self.actions)
                mutate(actions)
                with self.assertRaises(ValueError):
                    self.inspect(actions)

    def test_mismatched_source_schema_is_rejected(self):
        self.table["columns"][0]["type"] = "string"
        with self.assertRaisesRegex(ValueError, "schema differs"):
            self.inspect(self.actions)

    def test_manifest_path_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                safe_path(root, "../outside.parquet")
            self.assertEqual(safe_path(root, "parquet/fact.parquet"), Path(root).resolve() / "parquet/fact.parquet")

    def test_modified_manifest_is_rejected_before_data_loading(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "manifest.json").write_text('{"tampered": true}')
            (root / "manifest.sha256").write_text("0" * 64 + "  manifest.json\n")
            with self.assertRaisesRegex(ValueError, "Manifest checksum mismatch"):
                verify(root)

    def test_old_or_unverified_audit_is_rejected(self):
        audit = json.loads((Path(__file__).resolve().parents[1] / "metadata/e2e_star_verified_run.json").read_text())
        validate_audit(audit)
        for key, value in [("gold_run_id", "old_run"), ("gold_schema_version", 1), ("status", "pending")]:
            invalid = copy.deepcopy(audit)
            invalid[key] = value
            with self.assertRaises(ValueError):
                validate_audit(invalid)


if __name__ == "__main__":
    unittest.main()
