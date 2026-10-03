"""Local run identity and artifact integrity shared by both entry points."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path


def run_directory(output_root: Path, run_id: str) -> Path:
    if not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', run_id):
        raise ValueError('run_id must be 1-128 ASCII letters, digits, underscores or hyphens, starting with a letter/digit')
    if run_id.upper().split('.')[0] in {'CON', 'PRN', 'AUX', 'NUL', *[f'{p}{i}' for p in ('COM', 'LPT') for i in range(1, 10)]}:
        raise ValueError('Reserved run_id')
    root = output_root.resolve()
    runs = root / 'runs'
    target = runs / run_id
    if runs.resolve() != runs or target.resolve() != target:
        raise ValueError('Run directory must not traverse a symlink or junction')
    if not target.resolve().is_relative_to(runs):
        raise ValueError('Run directory escapes output/runs')
    return target


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inventory(root: Path, names: list[str]) -> dict:
    root = root.resolve()
    result = {}
    for name in names:
        target = root / name
        if not target.exists():
            raise RuntimeError(f'Missing artifact: {target}')
        paths = [target, *target.rglob('*')] if target.is_dir() else [target]
        files = 0
        for path in paths:
            if path.is_symlink() or path.resolve() != path or not path.resolve().is_relative_to(root):
                raise ValueError(f'Artifact traverses a link: {path}')
            if path.is_file():
                files += 1
                result[path.relative_to(root).as_posix()] = {'bytes': path.stat().st_size, 'sha256': digest(path)}
        if not files:
            raise RuntimeError(f'Empty artifact: {target}')
    return result


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    temporary.replace(path)


def bind_context(run_dir: Path, raw: Path, metadata: Path) -> None:
    project = Path(__file__).resolve().parents[1]
    context = {
        'version': 1,
        'raw_path': str(raw.resolve()), 'metadata_path': str(metadata.resolve()),
        'raw': inventory(raw, [p.name for p in sorted(raw.glob('*.csv'))]),
        'metadata': inventory(metadata, [p.name for p in sorted(metadata.glob('*.json'))]),
        'code': inventory(project, [p.relative_to(project).as_posix() for folder in ('src', 'scripts') for p in sorted((project / folder).glob('*.py'))]),
        'spark': {key: os.environ.get(key) for key in ('SPARK_MASTER', 'SPARK_SHUFFLE_PARTITIONS')},
    }
    if not context['raw'] or not context['metadata']:
        raise RuntimeError('Missing raw CSV or metadata inputs')
    path = run_dir / 'run_context.json'
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8')) != context:
            raise RuntimeError('Run inputs, code or configuration changed; use a new run_id')
    else:
        if any(run_dir.iterdir()):
            raise RuntimeError('Existing run has no integrity context; use a new run_id')
        write_json(path, context)
