"""Verify a Phase 12 bundle and restore it using only bundled data/libraries."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def verify(root):
    root = root.resolve()
    manifest = root / 'manifest.json'
    if digest(manifest) != (root / 'manifest.sha256').read_text().strip():
        raise ValueError('Manifest checksum mismatch')
    data = json.loads(manifest.read_text(encoding='utf-8'))
    expected = {'manifest.json', 'manifest.sha256'}
    for name, item in data['files'].items():
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Unsafe bundle path')
        if not path.is_file() or path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise ValueError(f'Bundle checksum mismatch: {name}')
        expected.add(name)
    if expected != {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}:
        raise ValueError('Bundle has unexpected or missing files')
    return data


def extract(archive, destination):
    if destination.exists():
        raise ValueError('Extraction destination must be new')
    destination.mkdir(parents=True)
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            target = destination / member.filename
            if not target.resolve().is_relative_to(destination.resolve()):
                raise ValueError('Unsafe ZIP entry')
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('ZIP symlinks are not allowed')
        if z.testzip() is not None:
            raise ValueError('ZIP CRC mismatch')
        z.extractall(destination)


def restore(root, output):
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):
        raise ValueError('Run with python -I -S -B')
    root, output = root.resolve(), output.resolve()
    if output.exists() or output.is_relative_to(root):
        raise ValueError('Use a new output directory outside the bundle')
    manifest = verify(root)
    output.mkdir(parents=True)
    report = {'status': 'failed', 'started_at_utc': datetime.now(timezone.utc).isoformat(),
              'bundle_files_verified': len(manifest['files']), 'credentials_forwarded': False,
              'source': 'Only files inside the extracted Phase 12 archive'}
    try:
        baseline = output / 'baseline'
        extract(root / 'baseline/ev-analytics-backup.zip', baseline)
        backup = baseline / 'ev-analytics-backup'
        runtime_home = output / 'runtime-home'
        runtime_home.mkdir()
        env = {k: os.environ[k] for k in ('SYSTEMROOT', 'WINDIR', 'COMSPEC') if k in os.environ}
        env.update(TEMP=str(runtime_home), TMP=str(runtime_home), USERPROFILE=str(runtime_home),
                   PATH=str(Path(sys.executable).parent))
        command = [sys.executable, '-I', '-S', '-B', str(backup / 'code/scripts/phase9_restore.py'),
                   '--backup', str(backup), '--output', str(output / 'baseline_verification')]
        report['baseline_command'] = command
        with (output / 'baseline_restore.log').open('w', encoding='utf-8') as log:
            subprocess.run(command, cwd=output, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        baseline_report = json.loads((output / 'baseline_verification/restore_report.json').read_text(encoding='utf-8'))
        if baseline_report['status'] != 'passed':
            raise ValueError('Baseline restore failed')
        report['baseline_restore'] = baseline_report['sql_restore']
        report['baseline_isolation'] = baseline_report['isolation']
        sys.path[:0] = [str(root / 'runtime'), str(root / 'project'), str(root / 'project/scripts')]
        from src.run_contract import inventory
        from phase11_reconcile import reconcile
        snapshot = root / 'snapshots/phase11'
        marker = json.loads((snapshot / 'published.json').read_text())
        if marker['status'] != 'published' or inventory(snapshot, ['run_context.json', 'bronze', 'silver', 'gold']) != marker['artifacts']:
            raise ValueError('Snapshot publish/integrity mismatch')
        comparison = reconcile(root / 'reference/phase10/gold', snapshot / 'gold')
        write_json(output / 'phase11_reconciliation.json', comparison)
        if comparison['status'] != 'passed':
            raise ValueError('Restored Phase 11 Gold differs from Phase 10')
        report['phase11_snapshot_files'] = len(marker['artifacts'])
        report['gold_tables_reconciled'] = len(comparison['tables'])
        report['status'] = 'passed'
    except Exception as exc:
        report['error'] = str(exc)
        raise
    finally:
        report['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        report['limitations'] = ['Windows x64 CPython 3.13 required for bundled native libraries',
                                'Phase 9 restore has a Python process audit guard; outer restore is not an OS network sandbox',
                                'Spark/Java/Airflow and cloud services are not bundled; this command verifies recovery, not a fresh cloud deployment']
        write_json(output / 'restore_report.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    restore(args.bundle, args.output)
