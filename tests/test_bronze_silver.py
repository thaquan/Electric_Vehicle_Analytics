import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from bronze_silver import validate_frame, transform


class QualityTests(unittest.TestCase):
    def validate(self, rows):
        frame = pd.DataFrame(rows, columns=["id", "Age", "Will_Buy_EV"])
        entry = {"columns": list(frame), "data_rows": 2}
        categories = [{"name": "Will_Buy_EV", "value_counts": {"Yes": 1, "No": 1}}]
        profile = {"column_profiles": [{"name": "id", "min": 0, "max": 1}, {"name": "Age", "min": 25, "max": 70}]}
        return validate_frame(frame, entry, categories, profile, "id")

    def test_valid_and_observed_bound_warning(self):
        errors, warnings = self.validate([["0", "24", "Yes"], ["1", "30", "No"]])
        self.assertEqual(errors, [])
        self.assertTrue(warnings)

    def test_duplicate_after_numeric_cast(self):
        errors, _ = self.validate([["0", "25", "Yes"], ["00", "30", "No"]])
        self.assertTrue(any("duplicate" in e for e in errors))

    def test_invalid_numeric_and_target(self):
        errors, _ = self.validate([["0", "NaN", "Maybe"], ["1", "30.5", "No"]])
        self.assertTrue(any("numeric" in e for e in errors))
        self.assertTrue(any("integer" in e for e in errors))
        self.assertTrue(any("Yes/No" in e for e in errors))

    def test_test_has_no_derived_target(self):
        result = transform(pd.DataFrame({"id": ["2"]}), "test", {"name": "test.csv", "sha256": "abc"}, "now")
        self.assertNotIn("will_buy_ev_flag", result)
        self.assertEqual(result.record_key.iloc[0], "test:2")

    def test_original_nulls_preserved_but_null_drift_fails(self):
        frame = pd.DataFrame({"Buyer_ID": ["EV1", "EV2"], "Annual_Income_USD": ["", "40000"]})
        entry = {"columns": list(frame), "data_rows": 2}
        profile = {"column_profiles": [{"name": "Annual_Income_USD", "min": 30000, "max": 50000, "null_count": 1}]}
        errors, _ = validate_frame(frame, entry, [], profile, "Buyer_ID")
        self.assertEqual(errors, [])
        frame.loc[1, "Annual_Income_USD"] = ""
        errors, _ = validate_frame(frame, entry, [], profile, "Buyer_ID")
        self.assertTrue(any("null count" in e for e in errors))

    def test_decimal_precision_loss_rejected(self):
        frame = pd.DataFrame({"id": ["0"], "Daily_Commute_km": ["1.12345"]})
        entry = {"columns": list(frame), "data_rows": 1}
        profile = {"column_profiles": [{"name": "id", "min": 0, "max": 0}, {"name": "Daily_Commute_km", "min": 0, "max": 10}]}
        errors, _ = validate_frame(frame, entry, [], profile, "id")
        self.assertTrue(any("decimal" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
