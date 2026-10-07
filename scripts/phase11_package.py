"""Build a clean Databricks project with the serverless modules installed as src."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ('bronze.py', 'silver.py', 'gold.py', 'quality_checks.py')
METADATA = ('source_manifest.json', 'gold_spec.json', 'gold_expected_metrics.json',
            'star_expected_metrics.json')


def sha256(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def build_package(destination: Path, raw: Path, project: Path = ROOT) -> dict:
    destination, raw, project = destination.resolve(), raw.resolve(), project.resolve()
    if destination.exists():
        raise ValueError('Destination already exists; choose a new empty release path')
    # Explicit allowlist: never copy credentials, caches or arbitrary workspace files.
    sources = {f'src/{name}': project / 'databricks/runtime_src' / name for name in RUNTIME}
    sources.update({f'src/{name}': project / 'src' / name
                    for name in ('__init__.py', 'run_contract.py')})
    sources.update({f'scripts/{name}': project / 'scripts' / name
                    for name in ('gold_rules.py', 'star_schema.py')})
    sources.update({f'metadata/{name}': project / 'metadata' / name for name in METADATA})
    manifest = json.loads((project / 'metadata/source_manifest.json').read_text(encoding='utf-8-sig'))
    for entry in manifest['files']:
        name = entry['name']
        if Path(name).name != name or '/' in name or '\\' in name or not name.endswith('.csv'):
            raise ValueError(f'Invalid source filename: {name}')
        source = raw / name
        if source.stat().st_size != entry['bytes'] or sha256(source) != entry['sha256'].lower():
            raise ValueError(f'Source snapshot mismatch: {name}')
        sources[f'data/raw/kaggle/{name}'] = source
    for source in sources.values():
        if not source.is_file():
            raise ValueError(f'Missing package input: {source}')
    destination.mkdir(parents=True)
    files = {}
    for relative, source in sorted(sources.items()):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        checksum = sha256(target)
        if checksum != sha256(source):
            raise RuntimeError(f'Package copy mismatch: {relative}')
        files[relative] = {'bytes': target.stat().st_size, 'sha256': checksum}
    result = {'version': 1, 'platform': 'databricks-serverless',
              'runtime_overlay': {f'src/{n}': f'databricks/runtime_src/{n}' for n in RUNTIME},
              'files': files}
    (destination / 'package_manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='New project directory; must not exist')
    parser.add_argument('--raw', type=Path, default=ROOT / 'data/raw/kaggle')
    args = parser.parse_args()
    result = build_package(args.output, args.raw)
    print(json.dumps({'project': str(args.output.resolve()), 'files': len(result['files']),
                      'status': 'packaged'}, indent=2))


if __name__ == '__main__':
    main()
