"""Seal current project, the accepted baseline backup and Phase 11 data in one ZIP."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from phase12_restore import digest, extract, verify, write_json

ROOT = Path(__file__).resolve().parents[1]


def copy(source, target):
    if source.is_symlink():
        raise ValueError(f'Symlink is not a release input: {source}')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def tree(source, target):
    for path in sorted(source.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            copy(path, target / path.relative_to(source))


def build(destination):
    if destination.exists():
        raise ValueError('Choose a new release directory')
    baseline = ROOT / 'output/phase9/release-02/ev-analytics-backup.zip'
    accepted = json.loads((ROOT / 'output/phase9/release-02/acceptance.json').read_text(encoding='utf-8'))
    if digest(baseline) != accepted['archive_sha256']:
        raise ValueError('Baseline ZIP differs from accepted backup')
    destination.mkdir(parents=True)
    # Keep extraction paths short enough for native Windows tools and Parquet names.
    bundle = destination / 'handoff'
    files = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    source_paths = []
    for relative in sorted(set(files) - {''}):
        source = ROOT / relative
        if not source.is_file():
            continue
        if relative.startswith(('output/', 'data/raw/', '.git/', '.tools/', '.codex/', '.agents/', '.aws/')):
            raise ValueError(f'Unexpected source selection: {relative}')
        copy(source, bundle / 'project' / relative)
        source_paths.append(relative)
    copy(baseline, bundle / 'baseline/ev-analytics-backup.zip')
    run = 'phase11_20261006T013808Z'
    tree(ROOT / 'output/phase11_reconciliation' / run, bundle / 'snapshots/phase11')
    tree(ROOT / 'output/phase10/runs/review_fix_20261003_03/gold', bundle / 'reference/phase10/gold')
    # DuckDB is shipped for offline reconciliation; its native extension is platform specific.
    distribution = importlib.metadata.distribution('duckdb')
    for relative in distribution.files:
        if '..' in relative.parts or '__pycache__' in relative.parts or str(relative).endswith('.pyc'):
            continue
        copy(Path(distribution.locate_file(relative)), bundle / 'runtime' / relative)
    from phase9_backup import scan_secrets
    scan = scan_secrets(bundle)
    scan['method'] = 'Git-visible project selection and credential-pattern scan; native runtime excluded from text scan'
    scan['excluded'] = ['Git-ignored files', 'credential stores', '.git', 'native runtime text scan']
    write_json(bundle / 'secret_scan.json', scan)
    manifest = {'version': 1, 'phase': 12, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
                'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'source_note': 'Working tree snapshot; exact delivered versions are pinned by the file hashes, including uncommitted Phase 12 work',
                'source_files': source_paths, 'phase11_run': run, 'duckdb_version': distribution.version,
                'files': {p.relative_to(bundle).as_posix(): {'bytes': p.stat().st_size, 'sha256': digest(p)}
                          for p in sorted(bundle.rglob('*')) if p.is_file()}}
    write_json(bundle / 'manifest.json', manifest)
    (bundle / 'manifest.sha256').write_text(digest(bundle / 'manifest.json') + '\n')
    verify(bundle)
    archive = destination / 'ev-analytics-handoff.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for path in sorted(bundle.rglob('*')):
            if path.is_file():
                z.write(path, 'handoff/' + path.relative_to(bundle).as_posix())
    (destination / 'ev-analytics-handoff.zip.sha256').write_text(digest(archive) + '  ' + archive.name + '\n')
    extract(archive, destination / 'clean-room')
    verify(destination / 'clean-room/handoff')
    report = {'status': 'packaged', 'archive': str(archive), 'archive_sha256': digest(archive),
              'archive_bytes': archive.stat().st_size, 'files': len(manifest['files']),
              'base_commit': manifest['base_commit'], 'manifest_sha256': digest(bundle / 'manifest.json'),
              'phase11_run': run, 'secret_scan': scan}
    write_json(destination / 'package_report.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True, type=Path)
    build(parser.parse_args().destination.resolve())
