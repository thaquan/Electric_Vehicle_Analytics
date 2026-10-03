"""Failure-path tests for the independent backup inventory and isolation guard."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/phase9_restore.py'
spec = importlib.util.spec_from_file_location('phase9_restore', SCRIPT)
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)


class BackupIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'manifests').mkdir()
        (self.root / 'data.bin').write_bytes(b'original snapshot')
        self.entry = {'path': 'data.bin', 'bytes': 17, 'sha256': hashlib.sha256(b'original snapshot').hexdigest()}
        self.seal([self.entry])

    def seal(self, entries):
        path = self.root / 'manifests/package.json'
        path.write_text(json.dumps({'files': entries}))
        (self.root / 'manifests/package.sha256').write_text(restore.digest(path))

    def test_valid_inventory(self):
        self.assertEqual(len(restore.verify_inventory(self.root)['files']), 1)

    def test_changed_data_rejected(self):
        (self.root / 'data.bin').write_bytes(b'changed! snapshot')
        with self.assertRaisesRegex(ValueError, 'Checksum'):
            restore.verify_inventory(self.root)

    def test_missing_data_rejected(self):
        (self.root / 'data.bin').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing'):
            restore.verify_inventory(self.root)

    def test_unlisted_data_rejected(self):
        (self.root / 'extra.bin').write_bytes(b'cache')
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            restore.verify_inventory(self.root)

    def test_manifest_tampering_rejected(self):
        (self.root / 'manifests/package.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Manifest checksum'):
            restore.verify_inventory(self.root)

    def test_path_escape_rejected(self):
        for path in ['../outside.csv', str(self.root / 'data.bin')]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                restore.safe_path(self.root, path)

    def test_duplicate_inventory_rejected(self):
        self.seal([self.entry, self.entry])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            restore.verify_inventory(self.root)

    def test_grouped_segment_reconciliation_passes_and_rejects_mismatch(self):
        import sqlite3
        db = sqlite3.connect(':memory:')
        try:
            db.execute('CREATE TABLE dim_demo (demo_key INTEGER, segment TEXT)')
            db.executemany('INSERT INTO dim_demo VALUES (?,?)', [(1, 'A'), (2, 'B')])
            db.execute('CREATE TABLE fact_ev_purchase_intent (demo_key INTEGER, will_buy_ev_flag INTEGER)')
            db.executemany('INSERT INTO fact_ev_purchase_intent VALUES (?,?)', [(1, 1), (1, 0), (2, 1)])
            dimensions = [{'role': 'dim_demo', 'key': 'demo_key', 'attributes': ['segment']}]
            expected = [
                {'segment_dimension': 'segment', 'segment_value': 'A', 'respondent_count': 2, 'yes_count': 1},
                {'segment_dimension': 'segment', 'segment_value': 'B', 'respondent_count': 1, 'yes_count': 1},
            ]
            self.assertEqual(restore.verify_sql_segments(db, expected, dimensions), 2)
            broken = [dict(item) for item in expected]
            broken[0]['yes_count'] = 2
            with self.assertRaisesRegex(ValueError, 'segment mismatch'):
                restore.verify_sql_segments(db, broken, dimensions)
        finally:
            db.close()

    def test_guard_blocks_network_external_reads_and_processes(self):
        code = '''
import runpy, pathlib, subprocess, sys
m = runpy.run_path(sys.argv[1])
root = pathlib.Path(sys.argv[2]).resolve()
state, reads = m['install_guard'](root, root)
m['guard_self_test'](root)
try:
    subprocess.run([sys.executable, '-c', 'pass'])
except PermissionError:
    pass
else:
    raise AssertionError('subprocess escaped guard')
assert state == {'network_blocked': 1, 'file_blocked': 1, 'process_blocked': 1}, state
'''
        result = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code, str(SCRIPT), str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
