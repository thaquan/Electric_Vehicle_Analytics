from __future__ import annotations

import json
import sys
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from star_schema import DIMENSIONS


def _read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def verify_gold(spark: SparkSession, gold_dir: Path, metadata_dir: Path) -> dict:
    expected = _read_json(metadata_dir / 'gold_expected_metrics.json')
    star_expected = _read_json(metadata_dir / 'star_expected_metrics.json')
    fact = spark.read.parquet(str(gold_dir / 'fact_ev_purchase_intent.parquet')).cache()
    n = fact.count(); yes = fact.agg(F.sum('will_buy_ev_flag')).first()[0]; no = fact.where(F.col('Will_Buy_EV') == 'No').count()
    if (n, yes, no) != (expected['respondent_count'], expected['yes_count'], expected['no_count']):
        raise ValueError('Gold KPI mismatch')
    orphan = 0; dimension_rows = {}
    for d in DIMENSIONS:
        role, key = d['role'], d['key']
        dim = spark.read.parquet(str(gold_dir / f'{role}.parquet')).cache()
        rows = dim.count()
        if rows != star_expected['dimension_rows'][role] or dim.select(key).distinct().count() != rows:
            raise ValueError(f'Dimension mismatch: {role}')
        orphan += fact.join(dim.select(key), key, 'left_anti').count()
        dimension_rows[role] = rows
        dim.unpersist()
    if orphan:
        raise ValueError(f'Orphan keys: {orphan}')
    seg = spark.read.parquet(str(gold_dir / 'agg_ev_segments.parquet'))
    actual = {(r.segment_dimension, r.segment_value): (r.respondent_count, r.yes_count) for r in seg.collect()}
    wanted = {(r['segment_dimension'], r['segment_value']): (r['respondent_count'], r['yes_count']) for r in expected['segments']}
    if actual != wanted or len(actual) != 35:
        raise ValueError('Segment reconciliation mismatch')
    fact.unpersist()
    return {'status': 'passed', 'respondents': n, 'yes': yes, 'no': no, 'orphan_keys': orphan, 'segment_groups': len(actual), 'dimension_rows': dimension_rows, 'tables': 8}
