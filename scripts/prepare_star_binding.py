"""Prepare MCP table-update requests and endpoint SQL from a VERIFIED v2 audit.

Does not deploy or edit the semantic model itself. Run the emitted request via
Power BI Modeling MCP table_operations.Update, then export and validate TMDL.
"""
import argparse
import json
from pathlib import Path

from pipeline_contract import check_run_id, check_pipeline_id
from star_schema import DIMENSIONS, FACT_ROLE
from star_sql import endpoint_sql

ROOT = Path(__file__).resolve().parents[1]


def binding_request(audit, connection_name):
    if audit.get('status') != 'verified' or audit.get('stage') != 'e2e' or audit.get('gold_schema_version') != 2:
        raise ValueError('A verified E2E star v2 audit is required; legacy Gold is not compatible')
    check_run_id(audit['gold_run_id'])
    check_run_id(audit['silver_run_id'])
    check_pipeline_id(audit['pipeline_run_id'], required=True)
    star = audit.get('star_validation', {})
    sql = audit.get('sql_validation', {})
    expected = json.loads((ROOT / 'metadata/star_expected_metrics.json').read_text())
    if star.get('status') != 'passed' or sql.get('status') != 'passed' or star.get('dimension_rows') != expected['dimension_rows']:
        raise ValueError('Missing or mismatched star/SQL checks')
    names = {r['role']: r['table'] for r in audit['tables']}
    counts = {r['role']: r['rows'] for r in audit['tables']}
    required = {FACT_ROLE: expected['fact_rows'], 'agg_ev_kpi': 1, 'agg_ev_segments': 35, **expected['dimension_rows']}
    if len(audit['tables']) != len(required) or counts != required:
        raise ValueError('Incomplete table set or row counts')
    for role, table in names.items():
        if table != role + '_' + audit['gold_run_id'].lower():
            raise ValueError('Mixed snapshot table binding')
    definitions = [{'name': 'EV Respondents', 'entityName': names[FACT_ROLE], 'expressionSourceName': 'GoldLakehouse', 'schemaName': 'dbo'}]
    definitions += [{'name': d['model'], 'entityName': names[d['role']], 'expressionSourceName': 'GoldLakehouse', 'schemaName': 'dbo'} for d in DIMENSIONS]
    return {'request': {'operation': 'Update', 'connectionName': connection_name, 'definitions': definitions}}, names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--connection-name', required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text(encoding='utf-8-sig'))
    request, names = binding_request(audit, args.connection_name)
    (ROOT / 'metadata/star_model_binding_request.json').write_text(json.dumps(request, indent=2) + '\n', encoding='utf-8')
    spec = json.loads((ROOT / 'metadata/gold_spec.json').read_text())
    path = ROOT / 'sql/gold_reconciliation.sql'
    path.parent.mkdir(exist_ok=True)
    path.write_text(endpoint_sql(names, DIMENSIONS, spec['segments'], 'silver_train_' + audit['silver_run_id'].lower()), encoding='utf-8')
    print('Prepared MCP binding request and SQL. Apply through Modeling MCP, export TMDL, refresh and execute DAX.')


if __name__ == '__main__':
    main()
