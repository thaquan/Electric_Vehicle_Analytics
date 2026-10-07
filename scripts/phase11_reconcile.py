"""Compare the eight Gold tables, retaining duplicate rows and schema checks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

TABLES = frozenset(('agg_ev_kpi', 'agg_ev_segments', 'dim_attitude_incentive',
                    'dim_charging', 'dim_demographics', 'dim_income',
                    'dim_mobility', 'fact_ev_purchase_intent'))
IGNORE = frozenset(('processed_at_utc', 'silver_run_id', 'gold_run_id'))


def reconcile(reference: Path, candidate: Path) -> dict:
    reference, candidate = reference.resolve(), candidate.resolve()
    result = {'phase10_run': reference.parent.name, 'phase11_run': candidate.parent.name,
              'reference_gold': str(reference), 'candidate_gold': str(candidate),
              'ignored_lineage_value_columns': sorted(IGNORE), 'tables': {}, 'status': 'passed'}
    for label, folder in (('reference', reference), ('candidate', candidate)):
        names = {p.name[:-8] for p in folder.glob('*.parquet')}
        if names != TABLES:
            result.update(status='failed', error=f'{label}: expected exactly eight Gold tables',
                          missing_tables=sorted(TABLES - names), extra_tables=sorted(names - TABLES))
            return result
    with duckdb.connect() as con:
        for role in sorted(TABLES):
            try:
                schemas, counts = [], []
                for alias, base in (('ref', reference), ('candidate', candidate)):
                    path = base / f'{role}.parquet'
                    pattern = str(path / '*.parquet' if path.is_dir() else path)
                    # Bind the path through DuckDB's relation API, never SQL interpolation.
                    con.read_parquet(pattern).create_view(alias, replace=True)
                    schemas.append([(r[0], r[1]) for r in con.execute(f'DESCRIBE {alias}').fetchall()])
                    counts.append(con.execute(f'SELECT count(*) FROM {alias}').fetchone()[0])
                same_schema = schemas[0] == schemas[1]
                columns = [[c for c, _ in schema if c not in IGNORE] for schema in schemas]
                same_columns = columns[0] == columns[1] and bool(columns[0])
                minus_ref = minus_candidate = None
                if same_schema and same_columns:
                    selection = ', '.join('"' + c.replace('"', '""') + '"' for c in columns[0])
                    def difference(left, right):
                        return con.execute(f'SELECT count(*) FROM ((SELECT {selection} FROM {left}) '
                                           f'EXCEPT ALL (SELECT {selection} FROM {right}))').fetchone()[0]
                    minus_ref, minus_candidate = difference('ref', 'candidate'), difference('candidate', 'ref')
                passed = same_schema and same_columns and counts[0] == counts[1] and minus_ref == minus_candidate == 0
                result['tables'][role] = {
                    'phase10_rows': counts[0], 'phase11_rows': counts[1], 'schema_equal': same_schema,
                    'non_lineage_columns_equal': same_columns, 'phase10_minus_phase11_rows': minus_ref,
                    'phase11_minus_phase10_rows': minus_candidate, 'status': 'passed' if passed else 'failed'}
            except (duckdb.Error, OSError) as exc:
                result['tables'][role] = {'status': 'failed', 'error': str(exc)}
            if result['tables'][role]['status'] != 'passed':
                result['status'] = 'failed'
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-gold', required=True, type=Path)
    parser.add_argument('--candidate-gold', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = reconcile(args.reference_gold, args.candidate_gold)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
