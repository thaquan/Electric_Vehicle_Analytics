"""Build a portable snapshot backup from local sources and downloaded Silver v0 files."""
import argparse
import importlib.util
import json
from pathlib import Path
import platform
import re
import shutil
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / '.tools/parquet-runtime'))
from export_gold_snapshot import arrow_schema, inspect_log, require, sha256, write_json
from build_recovery_package import include


def copy_file(source, target):
    require(not source.is_symlink(), f'Symlink not allowed: {source}')
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix == '.ipynb':
        doc = json.loads(source.read_text(encoding='utf-8-sig'))
        for cell in doc['cells']:
            if cell['cell_type'] == 'code':
                cell['outputs'], cell['execution_count'] = [], None
        doc.get('metadata', {}).pop('widgets', None)
        write_json(target, doc)
    else:
        shutil.copyfile(source, target)


def copy_folder(source, target):
    require(source.is_dir(), f'Missing source directory: {source}')
    for path in sorted(source.rglob('*')):
        if path.is_file() and include(path.relative_to(source)):
            copy_file(path, target / path.relative_to(source))


def scan_secrets(root):
    # Scan text assets, never echo matched values. Placeholders are allowed.
    patterns = [r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                r'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}',
                r'(?i)Bearer\s+[A-Za-z0-9._~-]{24,}',
                r'(?i)[?&]sig=[A-Za-z0-9%+/=]{20,}',
                r'''(?i)["']?(?:client_secret|password|access_token|refresh_token)["']?\s*[:=]\s*["'][A-Za-z0-9+/_=.~!-]{16,}["']''']
    checked = 0
    for path in root.rglob('*'):
        if not path.is_file() or 'runtime' in path.relative_to(root).parts:
            continue
        if path.suffix.lower() not in {'.py', '.json', '.md', '.txt', '.yaml', '.yml', '.tmdl', '.ipynb', '.sql', '.pbip', '.pbir', '.platform'}:
            continue
        content = path.read_text(encoding='utf-8-sig')
        require(not any(re.search(p, content) for p in patterns), f'Possible credential in {path.relative_to(root)}')
        checked += 1
    return {'status': 'passed', 'text_files_checked': checked,
            'method': 'allowlisted sources, stripped notebook outputs, credential-pattern scan',
            'excluded': ['credential stores', '.env', '.git', '.pbi', 'output journals', 'notebook outputs']}


def build(root, staging, gold):
    import pyarrow as pa
    import pyarrow.csv as pcsv
    import pyarrow.parquet as pq
    require(not root.exists(), 'Choose a new backup directory')
    root.mkdir(parents=True)
    for folder in ['data/raw', 'data/bronze', 'data/silver', 'code', 'fabric-definitions', 'powerbi', 'config', 'manifests', 'verification']:
        (root / folder).mkdir(parents=True, exist_ok=True)
    source = json.loads((PROJECT / 'metadata/source_manifest.json').read_text(encoding='utf-8-sig'))
    tables = []
    for entry in source['files']:
        raw = PROJECT / 'data/raw/kaggle' / entry['name']
        bronze = PROJECT / 'data/bronze' / entry['sha256'].lower() / entry['name']
        for path in [raw, bronze]:
            require(sha256(path).upper() == entry['sha256'].upper(), f'Source checksum: {path.name}')
        copy_file(raw, root / 'data/raw' / raw.name)
        copy_file(bronze, root / 'data/bronze' / bronze.name)
        table = pcsv.read_csv(bronze, convert_options=pcsv.ConvertOptions(column_types={c: pa.string() for c in entry['columns']}, strings_can_be_null=False))
        require(table.num_rows == entry['data_rows'] and table.column_names == entry['columns'], 'Bronze structure mismatch')
        dest = root / 'data/bronze' / (bronze.stem + '.parquet')
        pq.write_table(table, dest, compression='snappy')
        tables.append({'layer': 'bronze', 'name': bronze.stem, 'path': dest.relative_to(root).as_posix(),
                       'rows': table.num_rows, 'schema': str(table.schema), 'run_id': None,
                       'snapshot_id': entry['sha256'], 'run_id_note': 'Bronze is a content-addressed source snapshot, not a pipeline table.'})
    silver_run = '20260925T152449241452Z'
    for role, rows in [('train', 668665), ('test', 286571), ('original_reference', 10000)]:
        log = staging / (role + '.json')
        actions = [json.loads(line) for line in log.read_text().splitlines()]
        schema = json.loads(next(a['metaData']['schemaString'] for a in actions if 'metaData' in a))
        aliases = {'long': 'bigint', 'integer': 'int'}
        expected = {'rows': rows, 'columns': [{'name': f['name'], 'type': aliases.get(f['type'], f['type'])} for f in schema['fields']]}
        meta, schema, adds = inspect_log(log, expected)
        chunks, files = [], []
        for add in adds:
            path = staging / role / add['path']
            require(path.stat().st_size == add['size'], 'Incomplete Silver download')
            with path.open('rb') as stream:
                part = pq.read_table(stream, coerce_int96_timestamp_unit='us').cast(arrow_schema(schema), safe=True)
            require(part.num_rows == json.loads(add['stats'])['numRecords'], 'Silver source row mismatch')
            chunks.append(part)
            files.append({'path': add['path'], 'bytes': path.stat().st_size, 'sha256': sha256(path)})
        table = pa.concat_tables(chunks).combine_chunks()
        dest = root / 'data/silver' / (role + '.parquet')
        pq.write_table(table, dest, compression='snappy', version='2.6')
        require(table.equals(pq.read_table(dest)), 'Silver readback differs')
        copy_file(log, root / 'manifests/silver_source_logs' / (role + '.json'))
        tables.append({'layer': 'silver', 'name': 'silver_' + role + '_' + silver_run.lower(),
                       'role': role, 'path': dest.relative_to(root).as_posix(), 'rows': rows,
                       'schema': str(table.schema), 'delta_schema': schema, 'run_id': silver_run,
                       'delta_version': 0, 'delta_table_id': meta['id'], 'source_files': files,
                       'exact_export_readback': True})
    copy_file(staging / 'receipts.json', root / 'manifests/silver_download_receipts.json')
    copy_folder(gold, root / 'data/gold')
    gm = json.loads((gold / 'manifest.json').read_text())
    require(gm['silver_run_id'] == silver_run, 'Mixed Silver/Gold runs')
    for entry in gm['tables']:
        tables.append({'layer': 'gold', 'name': entry['source_table'], 'role': entry['role'],
                       'path': 'data/gold/' + entry['path'], 'rows': entry['rows'],
                       'schema': entry['arrow_schema'], 'run_id': gm['gold_run_id']})
    for name in ['scripts', 'tests', 'sql', 'notebooks', 'docs']:
        copy_folder(PROJECT / name, root / 'code' / name)
    for name in ['README.md', 'requirements.txt', 'requirements-export.txt', 'requirements-cd.txt', 'azure-pipelines.yml', 'azure-pipelines-test-cd.yml']:
        copy_file(PROJECT / name, root / 'code' / name)
    copy_folder(PROJECT / 'metadata', root / 'verification/source_metadata')
    copy_folder(PROJECT / 'config', root / 'config')
    for path in PROJECT.iterdir():
        if path.is_dir() and path.suffix in {'.Notebook', '.DataPipeline', '.Lakehouse'}:
            copy_folder(path, root / 'fabric-definitions' / path.name)
    for name in ['models', 'SM_EV_Analytics.SemanticModel', 'RPT_EV_Analytics.Report']:
        copy_folder(PROJECT / name, root / 'powerbi' / name)
    copy_file(PROJECT / 'RPT_EV_Analytics.pbip', root / 'powerbi/RPT_EV_Analytics.pbip')
    # Bundle native packages for the tested Windows CPython runtime, without caches.
    runtime = root / 'code/runtime'
    copy_folder(PROJECT / '.tools/parquet-runtime', runtime)
    for name in ['pandas', 'numpy', 'dateutil', 'tzdata', 'six']:
        spec = importlib.util.find_spec(name)
        origin = Path(spec.origin)
        if origin.name == '__init__.py':
            copy_folder(origin.parent, runtime / name)
            libs = origin.parent.parent / (name + '.libs')
            if libs.exists():
                copy_folder(libs, runtime / libs.name)
        else:
            copy_file(origin, runtime / origin.name)
        for dist in origin.parent.parent.glob(name.replace('dateutil', 'python_dateutil') + '-*.dist-info'):
            copy_folder(dist, runtime / dist.name)
    write_json(root / 'config/independent_restore.json', {
        'credentials_required_for_restore': [], 'data_root': '../data',
        'fabric_ids': 'Historical provenance only; independent restore does not use these IDs.',
        'optional_future_deployment_variables': ['AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET'],
        'silver_run_id': silver_run, 'gold_run_id': gm['gold_run_id'], 'pipeline_run_id': gm['pipeline_run_id']})
    copy_file(PROJECT / 'docs/phase9_backup.md', root / 'README.md')
    write_json(root / 'manifests/tables.json', tables)
    write_json(root / 'verification/secret_scan.json', scan_secrets(root))
    import pandas, numpy
    write_json(root / 'manifests/runtime.json', {'python': platform.python_version(), 'platform': platform.platform(),
        'architecture': platform.machine(), 'pandas': pandas.__version__, 'numpy': numpy.__version__, 'pyarrow': pa.__version__,
        'scope': 'Bundled packages for Windows x64 CPython 3.13; Python interpreter/stdlib must be installed separately.',
        'phase10_dependencies': 'Spark/Java/Airflow runtime is not bundled; phase 10 remains separate.'})
    inventory = {'version': 1, 'backup_id': root.name, 'gold_run_id': gm['gold_run_id'], 'silver_run_id': silver_run,
                 'delta_history': 'Portable snapshots only; saved Silver v0 logs are provenance, not full Delta backups.',
                 'files': [{'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha256(p)}
                           for p in sorted(root.rglob('*')) if p.is_file()]}
    write_json(root / 'manifests/package.json', inventory)
    (root / 'manifests/package.sha256').write_text(sha256(root / 'manifests/package.json') + '\n')
    print(json.dumps({'backup': str(root), 'files': len(inventory['files']), 'tables': len(tables)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--staging', type=Path, required=True)
    parser.add_argument('--gold', type=Path, required=True)
    args = parser.parse_args()
    build(args.destination.resolve(), args.staging.resolve(), args.gold.resolve())
