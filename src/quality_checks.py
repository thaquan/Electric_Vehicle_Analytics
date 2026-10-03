from __future__ import annotations

import json
import math
import sys
from functools import reduce
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from star_schema import DIMENSIONS, build_star_spark
from src.gold import enrich_train, _summarize


def _read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def check_aggregate_rows(rows: list[dict], wanted: dict, keys: tuple[str, ...]) -> None:
    actual = {}
    for row in rows:
        key = tuple(row.get(k) for k in keys)
        if any(k is None for k in key) or key in actual:
            raise ValueError('Duplicate/null aggregate key')
        n, yes = row.get('respondent_count'), row.get('yes_count')
        no, rate = row.get('no_count'), row.get('purchase_intent_rate')
        if (not isinstance(n, int) or not isinstance(yes, int) or n <= 0 or not 0 <= yes <= n
                or no != n - yes or not isinstance(rate, (int, float))
                or not math.isfinite(rate) or not math.isclose(rate, yes / n, rel_tol=1e-12, abs_tol=1e-15)):
            raise ValueError('Invalid aggregate counts/rate')
        actual[key] = (n, yes)
    if actual != wanted:
        raise ValueError('Aggregate reconciliation mismatch')


def verify_gold(spark: SparkSession, gold_dir: Path, metadata_dir: Path) -> dict:
    expected = _read_json(metadata_dir / 'gold_expected_metrics.json')
    star_expected = _read_json(metadata_dir / 'star_expected_metrics.json')
    spec = _read_json(metadata_dir / 'gold_spec.json')
    roles = ['fact_ev_purchase_intent', *[d['role'] for d in DIMENSIONS], 'agg_ev_kpi', 'agg_ev_segments']
    paths = {role: gold_dir / f'{role}.parquet' for role in roles}
    if {p.name for p in gold_dir.glob('*.parquet')} != {p.name for p in paths.values()}:
        raise ValueError('Gold must contain exactly the eight contracted tables')
    tables = {}
    cached = []
    try:
        for role, path in paths.items():
            tables[role] = spark.read.parquet(str(path)).cache()
            cached.append(tables[role])
        fact = tables['fact_ev_purchase_intent']
        stats = fact.agg(F.count('*').alias('n'), F.countDistinct('id').alias('ids'),
                         F.countDistinct('record_key').alias('keys'), F.sum('will_buy_ev_flag').alias('yes')).first()
        n, yes = stats.n, stats.yes
        no = fact.where(F.col('Will_Buy_EV') == 'No').count()
        if (n, yes, no) != (expected['respondent_count'], expected['yes_count'], expected['no_count']):
            raise ValueError('Gold KPI mismatch')
        if stats.ids != n or stats.keys != n:
            raise ValueError('Fact duplicate/null key')
        invalid_target = (F.col('Will_Buy_EV').isNull() | F.col('will_buy_ev_flag').isNull()
                          | ~F.col('Will_Buy_EV').isin('Yes', 'No')
                          | (F.col('will_buy_ev_flag') != F.when(F.col('Will_Buy_EV') == 'Yes', 1).otherwise(0)))
        if fact.where(invalid_target).limit(1).count():
            raise ValueError('Invalid fact target')
        dimension_rows = {}
        orphan = 0
        for d in DIMENSIONS:
            role, key = d['role'], d['key']
            dim = tables[role]
            rows = dim.count()
            if (rows != star_expected['dimension_rows'][role] or dim.select(key).distinct().count() != rows
                    or dim.where(F.col(key).isNull()).limit(1).count()):
                raise ValueError(f'Dimension mismatch: {role}')
            orphan += fact.join(dim.select(key), key, 'left_anti').count()
            dimension_rows[role] = rows
        if orphan:
            raise ValueError(f'Orphan keys: {orphan}')
        wanted_segments = {(r['segment_dimension'], r['segment_value']): (r['respondent_count'], r['yes_count']) for r in expected['segments']}
        segments = [r.asDict() for r in tables['agg_ev_segments'].collect()]
        check_aggregate_rows(segments, wanted_segments, ('segment_dimension', 'segment_value'))
        check_aggregate_rows([r.asDict() for r in tables['agg_ev_kpi'].collect()],
                             {('train',): (n, yes)}, ('source_dataset',))

        # Independently read Silver, rebuild expected tables and compare every field,
        # including dimension attributes, lineage and business keys. Parquet readers
        # relax nullability; compare Spark data types and values, not nullable flags.
        silver = spark.read.parquet(str(gold_dir.parent / 'silver/train.parquet'))
        enriched = enrich_train(silver, spec, gold_dir.parent.name, gold_dir.parent.name).cache()
        cached.append(enriched)
        reference = build_star_spark(enriched, spec['bands'])
        frames = [_summarize(enriched, [dimension]).withColumnRenamed(dimension, 'segment_value')
                  .withColumn('segment_value', F.col('segment_value').cast('string'))
                  .withColumn('segment_dimension', F.lit(dimension)) for dimension in spec['segments']]
        reference['agg_ev_segments'] = reduce(lambda a, b: a.unionByName(b), frames)
        reference['agg_ev_kpi'] = _summarize(enriched, []).withColumn('source_dataset', F.lit('train'))
        for role, frame in reference.items():
            if role.startswith('agg_'):
                frame = frame.withColumn('silver_run_id', F.lit(gold_dir.parent.name)).withColumn('gold_run_id', F.lit(gold_dir.parent.name))
            actual = tables[role]
            schema = lambda df: {f.name: f.dataType.simpleString() for f in df.schema}
            if schema(actual) != schema(frame):
                raise ValueError(f'Gold schema mismatch: {role}')
            columns = frame.columns
            if (actual.select(*columns).exceptAll(frame.select(*columns)).limit(1).count()
                    or frame.select(*columns).exceptAll(actual.select(*columns)).limit(1).count()):
                raise ValueError(f'Gold differs from Silver reconstruction: {role}')
        return {'status': 'passed', 'respondents': n, 'yes': yes, 'no': no, 'orphan_keys': orphan,
                'segment_groups': len(segments), 'dimension_rows': dimension_rows, 'tables': len(tables),
                'schema_checks': 'passed', 'silver_reconstruction': 'exact', 'aggregate_checks': 'passed'}
    finally:
        for frame in cached:
            frame.unpersist()
