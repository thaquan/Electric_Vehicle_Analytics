from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from pyspark.sql import SparkSession, types as T


def _sha256(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()


def _read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def build_bronze(spark: SparkSession, raw_dir: Path, metadata_dir: Path, output_dir: Path) -> dict:
    manifest = _read_json(metadata_dir / 'source_manifest.json')
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_dir = output_dir / 'csv'
    parquet_dir = output_dir / 'parquet'
    csv_dir.mkdir()
    parquet_dir.mkdir()
    tables = []
    for entry in manifest['files']:
        source = raw_dir / entry['name']
        if source.stat().st_size != entry['bytes'] or _sha256(source) != entry['sha256'].upper():
            raise ValueError(f'Source snapshot mismatch: {source.name}')
        copied = csv_dir / source.name
        shutil.copyfile(source, copied)
        if _sha256(copied) != entry['sha256'].upper():
            raise ValueError(f'Bronze copy checksum mismatch: {source.name}')
        schema = T.StructType([T.StructField(name, T.StringType(), True) for name in entry['columns']])
        frame = spark.read.option('header', True).option('mode', 'FAILFAST').schema(schema).csv(str(copied))
        if frame.count() != entry['data_rows'] or frame.columns != entry['columns']:
            raise ValueError(f'Bronze structure mismatch: {source.name}')
        target = parquet_dir / f"{source.stem}.parquet"
        frame.write.mode('error').parquet(str(target))
        tables.append({'name': source.stem, 'rows': entry['data_rows'], 'sha256': entry['sha256'], 'path': str(target)})
    return {'status': 'passed', 'tables': tables}
