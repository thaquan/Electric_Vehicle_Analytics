import json
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gold_rules import band_label, band_sql, require_gold_context, validate_band


class GoldTests(unittest.TestCase):
    def test_boundaries_and_sql_agree(self):
        spec = json.loads((ROOT / "metadata/gold_spec.json").read_text())
        with sqlite3.connect(":memory:") as db:
            for band in spec["bands"].values():
                cases = [(None, "Unknown")]
                for i, edge in enumerate(band["edges"]):
                    cases += [(edge - .01, band["labels"][i]), (edge, band["labels"][i + 1])]
                for value, expected in cases:
                    with self.subTest(column=band["column"], value=value):
                        self.assertEqual(band_label(value, band), expected)
                        actual = db.execute(f"SELECT {band_sql(band)} FROM (SELECT ? AS {band['column']})", (value,)).fetchone()[0]
                        self.assertEqual(actual, expected)

    def test_wrong_lakehouse_or_workspace_stops(self):
        config = {"gold_lakehouse_id": "gold", "workspace_id": "ev"}
        require_gold_context({"defaultLakehouseId": "gold", "defaultLakehouseWorkspaceId": "ev"}, config)
        for context in [{}, {"defaultLakehouseId": "silver", "defaultLakehouseWorkspaceId": "ev"}, {"defaultLakehouseId": "gold", "defaultLakehouseWorkspaceId": "other"}]:
            with self.assertRaises(RuntimeError):
                require_gold_context(context, config)

    def test_invalid_band_rejected(self):
        with self.assertRaises(ValueError):
            validate_band({"edges": [50, 25], "labels": ["a", "b", "c"]})

    def test_reference_segments_reconcile(self):
        reference = json.loads((ROOT / "metadata/gold_expected_metrics.json").read_text())
        spec = json.loads((ROOT / "metadata/gold_spec.json").read_text())
        for dimension in spec["segments"]:
            rows = [r for r in reference["segments"] if r["segment_dimension"] == dimension]
            self.assertEqual(sum(r["respondent_count"] for r in rows), spec["expected_rows"])
            self.assertEqual(sum(r["yes_count"] for r in rows), spec["expected_yes"])
            self.assertEqual(len(rows), len({r["segment_value"] for r in rows}))


if __name__ == "__main__":
    unittest.main()
