"""Restore only from a sealed backup. Run with python -I -S -B and no Fabric login."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_path(root, relative):
    path = Path(relative)
    require(not path.is_absolute() and not path.drive, 'Absolute inventory path')
    result = (root / path).resolve()
    require(result.is_relative_to(root.resolve()), 'Inventory path escapes backup')
    return result


def verify_inventory(root):
    manifest = root / 'manifests/package.json'
    require(digest(manifest) == (root / 'manifests/package.sha256').read_text().strip(), 'Manifest checksum mismatch')
    inventory = read_json(manifest)
    paths = [e['path'] for e in inventory['files']]
    require(len(paths) == len(set(paths)), 'Duplicate inventory path')
    expected = {'manifests/package.json', 'manifests/package.sha256'}
    for entry in inventory['files']:
        path = safe_path(root, entry['path'])
        require(not path.is_symlink() and path.is_file(), f'Missing inventory file: {entry["path"]}')
        require(path.stat().st_size == entry['bytes'] and digest(path) == entry['sha256'], f'Checksum mismatch: {entry["path"]}')
        expected.add(entry['path'])
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    require(actual == expected, 'Unexpected or missing backup files')
    return inventory


def install_guard(root, output):
    """Process guard for trusted restore code; not an OS/native-code sandbox."""
    allowed = [root.resolve(), output.resolve(), Path(sys.base_prefix).resolve()]
    state = {'network_blocked': 0, 'process_blocked': 0, 'file_blocked': 0}
    reads = set()

    def audit(event, args):
        if event.startswith('socket.'):
            state['network_blocked'] += 1
            raise PermissionError('Network is disabled for independent restore')
        if event in {'subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn', 'os.spawn'}:
            state['process_blocked'] += 1
            raise PermissionError('Child processes are disabled')
        if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            valid = any(path.is_relative_to(p) for p in allowed)
            if path.is_relative_to(Path(sys.base_prefix).resolve()) and 'site-packages' in path.parts:
                valid = False
            if not valid:
                state['file_blocked'] += 1
                raise PermissionError('Read outside backup/output/Python standard library')
            if path.is_relative_to(root):
                reads.add(path.relative_to(root).as_posix())
    sys.addaudithook(audit)
    return state, reads


def guard_self_test(root):
    import socket
    for action in [lambda: socket.getaddrinfo('onelake.dfs.fabric.microsoft.com', 443),
                   lambda: open(root.parent / 'forbidden_source_probe.csv', 'rb')]:
        try:
            action()
        except PermissionError:
            continue
        raise ValueError('Isolation self-test failed')


def validate_sources(root, output, tables):
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.csv as pcsv
    import pyarrow.parquet as pq
    from bronze_silver import prepare, SOURCES
    from export_gold_snapshot import arrow_schema
    metadata = root / 'verification/source_metadata'
    # Reuses source contract checks: categories, nullability, duplicate keys,
    # train/test separation, target distribution and submission order.
    frames = prepare(root / 'data/raw', metadata, output / 'source_quality.json')
    del frames
    manifest = read_json(metadata / 'source_manifest.json')
    checks = []
    for entry in manifest['files']:
        raw = root / 'data/raw' / entry['name']
        bronze_csv = root / 'data/bronze' / entry['name']
        require(digest(raw).upper() == digest(bronze_csv).upper() == entry['sha256'].upper(), 'Raw/Bronze source mismatch')
        csv = pcsv.read_csv(raw, convert_options=pcsv.ConvertOptions(column_types={c: pa.string() for c in entry['columns']}, strings_can_be_null=False))
        bronze = pq.read_table(root / 'data/bronze' / (Path(entry['name']).stem + '.parquet'))
        require(csv.equals(bronze), 'Bronze Parquet differs from original CSV')
        key = 'Buyer_ID' if 'Buyer_ID' in csv.column_names else 'id'
        values = csv[key].to_pylist()
        require(len(set(values)) == len(values) and all(v is not None and v != '' for v in values), 'Invalid Bronze primary key')
        checks.append({'layer': 'raw/bronze', 'file': entry['name'], 'rows': csv.num_rows,
                       'duplicate_keys': 0, 'missing_keys': 0, 'orphan_check': 'not applicable: independent source dataset'})
        role = next((r for r, n in SOURCES.items() if n == entry['name']), None)
        if role is None:
            continue
        record = next(t for t in tables if t['layer'] == 'silver' and t['role'] == role)
        silver = pq.read_table(safe_path(root, record['path']))
        require(silver.schema.equals(arrow_schema(record['delta_schema'])), 'Silver schema mismatch')
        require(silver.num_rows == entry['data_rows'], 'Silver row mismatch')
        for col in csv.column_names:
            values = csv[col]
            if role == 'original_reference':
                values = pc.if_else(pc.equal(values, ''), None, values)
            expected = pc.cast(values, silver.schema.field(col).type, safe=True)
            require(expected.equals(silver[col]), f'Silver source values differ: {role}/{col}')
        frame = silver.to_pandas()
        for key_name in [key, 'record_key']:
            require(frame[key_name].notna().all() and frame[key_name].is_unique, 'Invalid Silver keys')
        require(frame.record_key.eq(role + ':' + frame[key].astype(str)).all(), 'Silver record key mismatch')
        for name, value in [('source_dataset', role), ('source_file', entry['name']), ('source_sha256', entry['sha256'])]:
            require(frame[name].eq(value).all(), 'Silver provenance mismatch')
        require(frame.processed_at_utc.notna().all() and frame.processed_at_utc.nunique() == 1, 'Silver processing timestamp mismatch')
        if 'Will_Buy_EV' in frame:
            require(frame.will_buy_ev_flag.eq(frame.Will_Buy_EV.eq('Yes').astype(int)).all(), 'Silver target flag mismatch')
        checks.append({'layer': 'silver', 'table': record['name'], 'rows': len(frame), 'duplicate_keys': 0,
                       'missing_keys': 0, 'raw_reconstruction': 'exact (all business columns)',
                       'orphan_check': 'not applicable: independent source dataset', 'run_id': record['run_id']})
    # Gold fact + dimensions must reconstruct this exact Silver train snapshot.
    from star_schema import DIMENSIONS
    train = pq.read_table(root / 'data/silver/train.parquet').to_pandas().set_index('id').sort_index()
    fact = pq.read_table(root / 'data/gold/parquet/fact_ev_purchase_intent.parquet').to_pandas()
    for dim in DIMENSIONS:
        dimension = pq.read_table(root / 'data/gold/parquet' / (dim['role'] + '.parquet')).to_pandas()
        fact = fact.merge(dimension[[dim['key'], *dim['attributes']]], on=dim['key'], validate='many_to_one')
    fact = fact.set_index('id').sort_index()
    require(train.index.equals(fact.index), 'Silver/Gold ID mismatch')
    for col in train.columns:
        require(train[col].equals(fact[col]), f'Silver/Gold reconstruction differs: {col}')
    return checks


def verify_sql_segments(db, expected, dimensions):
    """Verify all expected segment rows with one grouped SQL scan per attribute."""
    allowed = {a for d in dimensions for a in d['attributes']}
    expected_by_col = {}
    for item in expected:
        col = item['segment_dimension']
        require(col in allowed, 'Unknown segment column')
        expected_by_col.setdefault(col, {})[item['segment_value']] = (
            item['respondent_count'], item['yes_count'])
    for col, expected_rows in expected_by_col.items():
        owner = next(d for d in dimensions if col in d['attributes'])
        role, key = owner['role'], owner['key']
        rows = db.execute(
            f'SELECT d."{col}", COUNT(*), COALESCE(SUM(f.will_buy_ev_flag),0) '
            f'FROM fact_ev_purchase_intent f JOIN {role} d ON f.{key}=d.{key} '
            f'GROUP BY d."{col}"'
        ).fetchall()
        actual = {value: (count, yes) for value, count, yes in rows}
        require(actual == expected_rows, f'Restored SQL segment mismatch: {col}')
    return sum(len(rows) for rows in expected_by_col.values())


def restore_tables(root, output, entries):
    import pyarrow as pa
    import pyarrow.parquet as pq
    import decimal
    restored = output / 'tables'
    restored.mkdir()
    catalog = []
    db = sqlite3.connect(output / 'ev_analytics.sqlite')
    try:
        for entry in entries:
            source = safe_path(root, entry['path'])
            with source.open('rb') as stream:
                table = pq.read_table(stream)
            require(table.num_rows == entry['rows'] and str(table.schema) == entry['schema'], 'Table rows/schema mismatch')
            name = entry['layer'] + '_' + entry.get('role', entry['name']) if entry['layer'] != 'gold' else entry['role']
            target = restored / (name + '.parquet')
            pq.write_table(table, target, compression='snappy', version='2.6')
            with target.open('rb') as stream:
                require(table.equals(pq.read_table(stream)), 'Restored Parquet differs')
            # SQLite stores decimals/timestamps as lossless text; exact Arrow types
            # remain in the restored Parquet files and catalog.
            types = ['INTEGER' if pa.types.is_integer(f.type) else 'REAL' if pa.types.is_floating(f.type) else 'TEXT' for f in table.schema]
            columns = ','.join('"' + f.name + '" ' + t for f, t in zip(table.schema, types))
            db.execute(f'CREATE TABLE "{name}" ({columns})')
            placeholders = ','.join('?' for _ in table.column_names)
            def scalar(value):
                return str(value) if isinstance(value, (decimal.Decimal, datetime)) else value
            for batch in table.to_batches(max_chunksize=10000):
                arrays = [a.to_pylist() for a in batch.columns]
                db.executemany(f'INSERT INTO "{name}" VALUES ({placeholders})',
                               (tuple(scalar(v) for v in row) for row in zip(*arrays)))
            count = db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            require(count == entry['rows'], 'SQL restore row mismatch')
            catalog.append({**entry, 'restored_table': name, 'restored_path': target.relative_to(output).as_posix(),
                            'restored_sha256': digest(target), 'sql_rows': count, 'parquet_exact_equality': True})
            print(f'Restored {name}: {count}', flush=True)
        db.commit()
        require(db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'SQLite integrity failed')
        n, yes, no = db.execute("SELECT COUNT(*), SUM(will_buy_ev_flag), SUM(CASE WHEN Will_Buy_EV='No' THEN 1 ELSE 0 END) FROM fact_ev_purchase_intent").fetchone()
        require((n, yes, no) == (668665, 116779, 551886), 'Restored SQL KPI mismatch')
        from star_schema import DIMENSIONS
        joins = []
        orphan = 0
        for d in DIMENSIONS:
            role, key = d['role'], d['key']
            orphan += db.execute(f'SELECT COUNT(*) FROM fact_ev_purchase_intent f LEFT JOIN {role} d ON f.{key}=d.{key} WHERE d.{key} IS NULL').fetchone()[0]
            joins.append(f'JOIN {role} ON f.{key}={role}.{key}')
        require(orphan == 0, 'Restored SQL orphan keys')
        expected = read_json(root / 'data/gold/evidence/gold_expected_metrics.json')['segments']
        segment_groups = verify_sql_segments(db, expected, DIMENSIONS)
        write_json(output / 'catalog.json', catalog)
        return {'respondents': n, 'yes': yes, 'no': no, 'orphan_keys': orphan, 'segment_groups': segment_groups, 'tables': len(catalog)}
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.backup.resolve(), args.output.resolve()
    require(not output.exists() and not output.is_relative_to(root), 'Use a new output directory outside the backup')
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, 'Run with python -I -S -B')
    output.mkdir(parents=True)
    report = {'status': 'failed', 'started_at_utc': datetime.now(timezone.utc).isoformat(), 'backup': str(root), 'output': str(output)}
    state, reads = install_guard(root, output)
    try:
        guard_self_test(root)
        state_after_probe = dict(state)
        inventory = verify_inventory(root)
        report['manifest_sha256'] = digest(root / 'manifests/package.json')
        report['inventory_files'] = len(inventory['files'])
        # Only bundled libraries and backup code; -S excludes machine site-packages.
        sys.path[:0] = [str(root / 'code/runtime'), str(root / 'code/scripts')]
        import pyarrow, pandas, numpy
        report['runtime'] = {'python': sys.version, 'pyarrow': pyarrow.__version__, 'pandas': pandas.__version__, 'numpy': numpy.__version__}
        state_after_setup = dict(state)
        entries = read_json(root / 'manifests/tables.json')
        report['source_checks'] = validate_sources(root, output, entries)
        from export_gold_snapshot import verify
        report['gold_validation'] = verify(root / 'data/gold')
        report['sql_restore'] = restore_tables(root, output, entries)
        require(state == state_after_setup, 'Unexpected blocked operation during restore')
        report['isolation'] = {'mode': 'Python audit guard, isolated imports, local file readers',
            'self_tests': 'network and outside-file reads denied',
            'self_test_blocked_operations': state_after_probe,
            'setup_blocked_operations': {k: state_after_setup[k] - state_after_probe[k] for k in state},
            'blocked_operations': state, 'unexpected_blocked_operations': 0, 'fabric_credentials_used': False,
            'limitation': 'Process-level protection for this trusted script, not an OS firewall or native-code sandbox.'}
        report['status'] = 'passed'
    except Exception as exc:
        report['error'] = str(exc)
        raise
    finally:
        report['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        write_json(output / 'input_paths.json', sorted(reads))
        write_json(output / 'restore_report.json', report)
    print(json.dumps({'status': report['status'], **report['sql_restore']}, indent=2))


if __name__ == '__main__':
    main()
