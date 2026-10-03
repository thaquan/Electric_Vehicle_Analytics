"""Archive a sealed backup and prove recovery from a new extraction of that ZIP."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from phase9_restore import digest, require, verify_inventory, write_json


def release(backup, destination):
    require(not destination.exists(), 'Choose a new release directory')
    inventory = verify_inventory(backup)
    destination.mkdir(parents=True)
    archive = destination / 'ev-analytics-backup.zip'
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(backup.rglob('*')):
            if path.is_file():
                z.write(path, 'ev-analytics-backup/' + path.relative_to(backup).as_posix())
    archive_hash = digest(archive)
    archive.with_suffix('.zip.sha256').write_text(archive_hash + '  ' + archive.name + '\n')
    clean = destination / 'clean-room'
    clean.mkdir()
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            target = (clean / member.filename).resolve()
            require(target.is_relative_to(clean.resolve()), 'ZIP path traversal')
        require(z.testzip() is None, 'ZIP CRC error')
        z.extractall(clean)
    extracted = clean / 'ev-analytics-backup'
    verify_inventory(extracted)
    script = extracted / 'code/scripts/phase9_restore.py'
    output = clean / 'verification'
    command = [sys.executable, '-I', '-S', '-B', str(script), '--backup', str(extracted), '--output', str(output)]
    env = {key: os.environ[key] for key in ('SYSTEMROOT', 'WINDIR', 'COMSPEC') if key in os.environ}
    runtime_home = clean / 'runtime-home'
    runtime_home.mkdir()
    env.update({'TEMP': str(runtime_home), 'TMP': str(runtime_home), 'USERPROFILE': str(runtime_home),
                'PATH': str(Path(sys.executable).parent)})
    write_json(destination / 'invocation.json', {'command': command, 'cwd': str(clean),
        'environment_keys': sorted(env), 'credentials_forwarded': False, 'source': 'Fresh extraction of delivered ZIP'})
    print('ZIP sealed; starting independent restore from extracted package.', flush=True)
    with (destination / 'restore.log').open('w', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=clean, env=env, stdout=log, stderr=subprocess.STDOUT)
    require(result.returncode == 0, f'Restore failed; inspect {destination / "restore.log"}')
    report = json.loads((output / 'restore_report.json').read_text(encoding='utf-8'))
    require(report['status'] == 'passed', 'Restore did not pass')
    evidence = destination / 'verification'
    evidence.mkdir()
    for name in ['restore_report.json', 'source_quality.json', 'input_paths.json', 'catalog.json']:
        shutil.copyfile(output / name, evidence / name)
    summary = {'status': 'passed', 'phase': 9, 'completed_at_utc': datetime.now(timezone.utc).isoformat(),
        'archive': str(archive), 'archive_sha256': archive_hash, 'archive_bytes': archive.stat().st_size,
        'manifest_sha256': report['manifest_sha256'], 'inventory_files': len(inventory['files']),
        'gold_run_id': inventory['gold_run_id'], 'silver_run_id': inventory['silver_run_id'],
        'restore_report': str(evidence / 'restore_report.json'), 'restore_report_sha256': digest(evidence / 'restore_report.json'),
        'result': report['sql_restore'], 'independent_restore': True, 'fabric_access_during_restore': False,
        'isolation': report['isolation'],
        'limitations': ['Snapshot backup, not full Delta history', 'Bundled libraries require Windows x64 CPython 3.13',
                       'Report/model definitions retained; not rendered outside Fabric', 'Full PySpark/Airflow pipeline is phase 10']}
    write_json(destination / 'acceptance.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    release(args.backup.resolve(), args.destination.resolve())
