from __future__ import annotations

import json
import sys
from functools import reduce
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from gold_rules import band_sql
from star_schema import build_star_spark


def _read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def enrich_train(frame, spec: dict, silver_run_id: str, gold_run_id: str):
    result = frame
    for name, band in spec['bands'].items():
        result = result.withColumn(name, F.expr(band_sql(band)))
    return result.withColumn('silver_run_id', F.lit(silver_run_id)).withColumn('gold_run_id', F.lit(gold_run_id))


def _summarize(frame, groups):
    summary = frame.groupBy(*groups).agg(F.count('*').alias('respondent_count'), F.sum('will_buy_ev_flag').alias('yes_count'))
    return summary.withColumn('no_count', F.col('respondent_count') - F.col('yes_count')).withColumn('purchase_intent_rate', F.col('yes_count') / F.col('respondent_count'))


def build_gold(spark: SparkSession, silver_dir: Path, metadata_dir: Path, output_dir: Path, silver_run_id: str, gold_run_id: str) -> dict:
    spec = _read_json(metadata_dir / 'gold_spec.json')
    expected = _read_json(metadata_dir / 'gold_expected_metrics.json')
    star_expected = _read_json(metadata_dir / 'star_expected_metrics.json')
    source = spark.read.parquet(str(silver_dir / 'train.parquet')).cache()
    stats = source.agg(F.count('*').alias('rows'), F.countDistinct('id').alias('keys'), F.sum('will_buy_ev_flag').alias('yes')).first()
    if (stats.rows, stats.keys, stats.yes) != (expected['respondent_count'], expected['respondent_count'], expected['yes_count']):
        raise ValueError('Silver counts, key or target totals mismatch')
    fact = enrich_train(source, spec, silver_run_id, gold_run_id).cache()
    for name in spec['bands']:
        if fact.where(F.col(name) == 'Unknown').limit(1).count():
            raise ValueError(f'Unexpected band value: {name}')
    segment_frames = []
    for dimension in spec['segments']:
        segment = _summarize(fact, [dimension]).withColumnRenamed(dimension, 'segment_value')
        segment_frames.append(segment.withColumn('segment_value', F.col('segment_value').cast('string')).withColumn('segment_dimension', F.lit(dimension)))
    segments = reduce(lambda a, b: a.unionByName(b), segment_frames).cache()
    actual = {(r.segment_dimension, r.segment_value): (r.respondent_count, r.yes_count) for r in segments.collect()}
    wanted = {(r['segment_dimension'], r['segment_value']): (r['respondent_count'], r['yes_count']) for r in expected['segments']}
    if actual != wanted:
        raise ValueError('Gold segment counts differ from baseline')
    kpi = _summarize(fact, []).withColumn('source_dataset', F.lit('train'))
    tables = build_star_spark(fact, spec['bands'])
    tables.update({'agg_ev_kpi': kpi, 'agg_ev_segments': segments})
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for role, frame in tables.items():
        if role != 'fact_ev_purchase_intent':
            frame = frame.withColumn('silver_run_id', F.lit(silver_run_id)).withColumn('gold_run_id', F.lit(gold_run_id))
        target = output_dir / f'{role}.parquet'
        frame.write.mode('errorifexists').parquet(str(target))
        rows = spark.read.parquet(str(target)).count()
        expected_rows = (expected['respondent_count'] if role == 'fact_ev_purchase_intent' else star_expected['dimension_rows'][role] if role.startswith('dim_') else 1 if role == 'agg_ev_kpi' else len(wanted))
        if rows != expected_rows:
            raise ValueError(f'Written row count mismatch: {role}')
        outputs.append({'role': role, 'rows': rows, 'path': str(target)})
    source.unpersist(); fact.unpersist(); segments.unpersist()
    return {'status': 'passed', 'silver_run_id': silver_run_id, 'gold_run_id': gold_run_id, 'tables': outputs}
