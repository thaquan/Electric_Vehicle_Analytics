from __future__ import annotations

import json
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

SOURCES = {'train': 'train', 'test': 'test', 'original_reference': 'EV_Adoption_and_Range_Anxiety_Dataset'}
INTEGERS = {'id', 'Age', 'Number_of_Cars_Owned', 'Charging_Stations_Near_Home', 'Charging_Stations_Near_Work'}
DECIMALS = {'Annual_Income_USD', 'Daily_Commute_km'}
ORIGINAL_NULLABLE = {'Annual_Income_USD', 'Daily_Commute_km', 'Environmental_Concern_Level'}


def _read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def build_silver(spark: SparkSession, bronze_dir: Path, metadata_dir: Path, output_dir: Path, run_id: str, processed_at_utc: str) -> dict:
    manifest = _read_json(metadata_dir / 'source_manifest.json')
    expected_by_name = {Path(e['name']).stem: e for e in manifest['files']}
    output_dir.mkdir(parents=True, exist_ok=True)
    published = []
    for source, stem in SOURCES.items():
        entry = expected_by_name[stem]
        frame = spark.read.parquet(str(bronze_dir / 'parquet' / f'{stem}.parquet'))
        if frame.count() != entry['data_rows']:
            raise ValueError(f'{source}: Bronze row count mismatch')
        if source == 'original_reference':
            for col in ORIGINAL_NULLABLE & set(frame.columns):
                frame = frame.withColumn(col, F.when(F.trim(F.col(col)) == '', None).otherwise(F.col(col)))
        for col in frame.columns:
            if col in INTEGERS:
                frame = frame.withColumn(col, F.col(col).cast('long' if col == 'id' else 'int'))
            elif col in DECIMALS:
                frame = frame.withColumn(col, F.col(col).cast('decimal(18,4)'))
        if 'Will_Buy_EV' in frame.columns:
            frame = frame.withColumn('will_buy_ev_flag', F.when(F.col('Will_Buy_EV') == 'Yes', 1).otherwise(0).cast('int'))
        key = 'Buyer_ID' if source == 'original_reference' else 'id'
        frame = (frame.withColumn('source_dataset', F.lit(source))
                 .withColumn('source_file', F.lit(entry['name']))
                 .withColumn('source_sha256', F.lit(entry['sha256']))
                 .withColumn('processed_at_utc', F.lit(processed_at_utc).cast('timestamp'))
                 .withColumn('record_key', F.concat(F.lit(source + ':'), F.col(key).cast('string'))))
        if source == 'test' and ('Will_Buy_EV' in frame.columns or 'will_buy_ev_flag' in frame.columns):
            raise ValueError('Test target leakage')
        target = output_dir / f'{source}.parquet'
        frame.write.mode('error').parquet(str(target))
        rows = spark.read.parquet(str(target)).count()
        if rows != entry['data_rows']:
            raise ValueError(f'{source}: written row count mismatch')
        published.append({'role': source, 'rows': rows, 'path': str(target)})
    return {'status': 'passed', 'run_id': run_id, 'tables': published}
