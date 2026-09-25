"""Independent full-snapshot pandas/SQLite reference; never claims a Fabric run."""
import hashlib
import json
import sqlite3
from pathlib import Path

import pandas as pd
from gold_rules import band_label
from star_schema import DIMENSIONS, FACT_ROLE, dimension_key
from star_sql import star_queries, check_sql_results

ROOT = Path(__file__).resolve().parents[1]


def build_reference(frame, spec):
    frame = frame.copy()
    frame['will_buy_ev_flag'] = frame.Will_Buy_EV.map({'Yes': 1, 'No': 0})
    for name, band in spec['bands'].items():
        frame[name] = frame[band['column']].map(lambda x: band_label(x, band))
    dimensions = {}
    fact = frame.copy()
    for d in DIMENSIONS:
        attrs, key = d['attributes'], d['key']
        dim = frame[attrs].drop_duplicates().copy()
        dim[key] = [dimension_key(d['role'], values) for values in dim.itertuples(index=False, name=None)]
        for attr in attrs:
            if attr in spec['bands']:
                dim[attr + '_sort'] = dim[attr].map({v: i + 1 for i, v in enumerate(spec['bands'][attr]['labels'])})
        if dim[key].duplicated().any() or dim.isna().any().any():
            raise ValueError('Invalid dimension')
        fact = fact.merge(dim[attrs + [key]], on=attrs, how='left', validate='many_to_one')
        dimensions[d['role']] = dim
    removed = {a for d in DIMENSIONS for a in d['attributes']}
    fact = fact.drop(columns=list(removed))
    return frame, fact, dimensions


def validate_reference(source, fact, dimensions):
    if fact.id.isna().any() or fact.id.duplicated().any() or len(fact) != len(source):
        raise ValueError('Fact grain mismatch')
    restored = fact.copy()
    for d in DIMENSIONS:
        dim, key = dimensions[d['role']], d['key']
        if dim[key].isna().any() or dim[key].duplicated().any() or dim.duplicated(d['attributes']).any():
            raise ValueError('Duplicate/null dimension key or business attributes')
        if fact[key].isna().any() or not fact[key].isin(dim[key]).all():
            raise ValueError('Orphan fact key')
        restored = restored.merge(dim[[key] + d['attributes']], on=key, validate='many_to_one')
    try:
        pd.testing.assert_frame_equal(source.sort_values('id').reset_index(drop=True),
                                      restored[source.columns].sort_values('id').reset_index(drop=True), check_dtype=False)
    except AssertionError as exc:
        raise ValueError('Star reconstruction differs from source') from exc


def main():
    spec = json.loads((ROOT / 'metadata/gold_spec.json').read_text())
    expected = json.loads((ROOT / 'metadata/gold_expected_metrics.json').read_text())
    path = ROOT / 'data/raw/kaggle/train.csv'
    with path.open('rb') as f:
        if hashlib.file_digest(f, 'sha256').hexdigest().upper() != expected['source_sha256']:
            raise ValueError('Snapshot hash mismatch')
    frame = pd.read_csv(path, dtype={'Environmental_Concern_Level': str})
    source, fact, dims = build_reference(frame, spec)
    validate_reference(source, fact, dims)
    names = {r: r for r in [FACT_ROLE, *dims]}
    queries = star_queries(names, DIMENSIONS, spec['segments'])
    with sqlite3.connect(':memory:') as db:
        db.row_factory = sqlite3.Row
        fact.to_sql(FACT_ROLE, db, index=False)
        for name, dim in dims.items():
            dim.to_sql(name, db, index=False)
        kpi = dict(db.execute(queries['kpi']).fetchone())
        segments = [dict(r) for r in db.execute(queries['segments']).fetchall()]
        check_sql_results(kpi, segments, expected)
    result = {'gold_schema_version': 2, 'verification_scope': 'Full local train snapshot: pandas reconstruction and SQLite SQL; not Fabric execution',
              'source_sha256': expected['source_sha256'], 'fact_rows': len(fact),
              'dimension_rows': {name: len(dim) for name, dim in dims.items()},
              'reconstruction': 'passed', 'orphan_keys': 0, 'kpi_sql': kpi, 'segments_sql': segments}
    (ROOT / 'metadata/star_expected_metrics.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'segments_sql'}, indent=2))


if __name__ == '__main__':
    main()
