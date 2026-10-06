import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import duckdb

from scripts.phase11_package import ROOT, RUNTIME, build_package, sha256
from scripts.phase11_reconcile import TABLES, reconcile


class Phase11Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def tables(self, folder, values='(1), (1), (2)', lineage='run'):
        folder.mkdir()
        with duckdb.connect() as con:
            for role in TABLES:
                con.sql(f"SELECT v AS id, '{lineage}' AS gold_run_id FROM (VALUES {values}) t(v)").write_parquet(
                    str(folder / f'{role}.parquet'))

    def test_lineage_changes_allowed_but_duplicate_multiplicity_detected(self):
        a, b = self.base / 'a', self.base / 'b'
        self.tables(a, lineage='a')
        self.tables(b, lineage='b')
        self.assertEqual(reconcile(a, b)['status'], 'passed')
        with duckdb.connect() as con:
            con.sql("SELECT v AS id, 'b' AS gold_run_id FROM (VALUES (1), (2), (2)) t(v)").write_parquet(
                str(b / 'fact_ev_purchase_intent.parquet'))
        result = reconcile(a, b)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['tables']['fact_ev_purchase_intent']['phase10_minus_phase11_rows'], 1)

    def test_empty_or_missing_tables_cannot_pass(self):
        self.assertEqual(reconcile(self.base / 'absent', self.base / 'absent')['status'], 'failed')
        a, b = self.base / 'a', self.base / 'b'
        self.tables(a)
        self.tables(b)
        (b / 'agg_ev_kpi.parquet').unlink()
        self.assertEqual(reconcile(a, b)['status'], 'failed')

    def test_lineage_schema_still_checked(self):
        a, b = self.base / 'a', self.base / 'b'
        self.tables(a)
        self.tables(b)
        with duckdb.connect() as con:
            con.sql('SELECT v AS id, 123 AS gold_run_id FROM (VALUES (1), (1), (2)) t(v)').write_parquet(
                str(b / 'agg_ev_kpi.parquet'))
        result = reconcile(a, b)
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['tables']['agg_ev_kpi']['schema_equal'])

    def test_package_imports_serverless_modules_from_clean_directory(self):
        # Small source fixture; all actual production modules and metadata are copied.
        project, raw = self.base / 'source', self.base / 'raw'
        import shutil
        for folder in ('src', 'scripts', 'metadata', 'databricks/runtime_src'):
            target = project / folder
            target.mkdir(parents=True, exist_ok=True)
            for p in (ROOT / folder).glob('*'):
                if p.is_file() and p.suffix in ('.py', '.json'):
                    shutil.copyfile(p, target / p.name)
        raw.mkdir()
        source = raw / 'train.csv'
        source.write_text('id\n1\n')
        (project / 'metadata/source_manifest.json').write_text(json.dumps({'files': [
            {'name': 'train.csv', 'bytes': source.stat().st_size, 'sha256': sha256(source)}]}))
        output = self.base / 'package'
        result = build_package(output, raw, project)
        for name in RUNTIME:
            self.assertEqual(sha256(output / 'src' / name), sha256(ROOT / 'databricks/runtime_src' / name))
        for name, details in result['files'].items():
            self.assertEqual(sha256(output / name), details['sha256'])
        check = """import pathlib, src.bronze, src.silver, src.gold, src.quality_checks
for m in (src.bronze, src.silver, src.gold, src.quality_checks):
 assert pathlib.Path(m.__file__).parent == pathlib.Path.cwd() / 'src'
 assert '.cache()' not in pathlib.Path(m.__file__).read_text()
assert src.quality_checks.enrich_train is src.gold.enrich_train
"""
        subprocess.run([sys.executable, '-c', check], cwd=output, check=True, capture_output=True)
        with self.assertRaises(ValueError):
            build_package(output, raw, project)
        source.write_text('id\n2\n')
        with self.assertRaisesRegex(ValueError, 'snapshot mismatch'):
            build_package(self.base / 'bad', raw, project)
        self.assertFalse((self.base / 'bad').exists())


if __name__ == '__main__':
    unittest.main()
