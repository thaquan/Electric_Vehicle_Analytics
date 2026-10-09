import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_source_download import verify


class DownloadVerificationTests(unittest.TestCase):
    def test_missing_tampered_and_matching_downloads(self):
        expected = b"id,value\n1,Yes\n"
        manifest = {"files": [{"name": "train.csv", "bytes": len(expected),
                               "sha256": hashlib.sha256(expected).hexdigest().upper()}]}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(verify(root, manifest)[0]["status"], "missing")
            (root / "train.csv").write_bytes(expected.replace(b"Yes", b"No!"))
            self.assertEqual(verify(root, manifest)[0]["status"], "mismatch")
            (root / "train.csv").write_bytes(expected)
            self.assertEqual(verify(root, manifest)[0]["status"], "matched")

    def test_competition_scope_does_not_claim_reference_file_verified(self):
        entry = {"name": "EV_Adoption_and_Range_Anxiety_Dataset.csv", "bytes": 0,
                 "sha256": hashlib.sha256(b"").hexdigest()}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(verify(root, {"files": [entry]}, competition_only=True), [])
            self.assertEqual(verify(root, {"files": [entry]})[0]["status"], "missing")

    def test_manifest_cannot_escape_download_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                verify(Path(folder), {"files": [{"name": "../train.csv"}]})


if __name__ == "__main__":
    unittest.main()
