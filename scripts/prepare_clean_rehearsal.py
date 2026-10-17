"""Snapshot versioned and non-ignored source for an isolated rehearsal.

Never copies raw data, Git internals or ignored local runtime/output folders.
The inventory identifies working-tree bytes, including uncommitted changes;
it does not claim CI provenance. Existing destinations are never overwritten.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def prepare(output):
    output = output.resolve()
    if not output.is_relative_to(ROOT / 'output') or output == ROOT / 'output':
        raise ValueError('Select a new subdirectory under output/')
    if output.exists():
        raise ValueError('Destination exists; preserve the earlier rehearsal')
    names = sorted(set(git('ls-files', '-c', '-o', '--exclude-standard', '-z').decode('utf-8').split('\0')) - {''})
    inventory = {}
    for name in names:
        source = ROOT / name
        if source.is_symlink() or not source.resolve().is_relative_to(ROOT):
            raise ValueError('Source must remain inside repository: ' + name)
        if source.is_file():
            inventory[name] = hashlib.sha256(source.read_bytes()).hexdigest()
    output.mkdir(parents=True)
    for name, checksum in inventory.items():
        target = output / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
        if hashlib.sha256(target.read_bytes()).hexdigest() != checksum:
            raise ValueError('Source changed while copying: ' + name)
    manifest = {
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'base_commit': git('rev-parse', 'HEAD').decode().strip(),
        'working_tree_dirty': bool(git('status', '--porcelain').strip()),
        'scope': 'Working-tree source snapshot; separate raw input and fresh virtual environment required',
        'files': inventory,
    }
    (output / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'source': str(output / 'source'), 'files': len(inventory),
                      'working_tree_dirty': manifest['working_tree_dirty']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    prepare(parser.parse_args().output)
