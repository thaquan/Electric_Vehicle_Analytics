import copy
import json
import sqlite3
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from profile_star import build_reference, validate_reference
from star_schema import DIMENSIONS, FACT_ROLE, dimension_key
from star_sql import star_queries, check_sql_results, endpoint_sql
from pipeline_contract import require_publication
from prepare_star_binding import binding_request


class StarTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((ROOT / 'metadata/gold_spec.json').read_text())
        # Same dimension tuple for two respondents; one other tuple. Joins must
        # preserve two facts while dimensions deduplicate, even at band edges.
        frame = pd.DataFrame([
            dict(id=i, Age=age, Gender='Female', City_Type='Urban', Annual_Income_USD=income,
                 Daily_Commute_km=commute, Current_Car_Type='Petrol', Home_Charging_Possible='Yes',
                 Environmental_Concern_Level='1.0', Subsidy_Available='No', Range_Anxiety_Level='High',
                 Will_Buy_EV=target)
            for i, age, income, commute, target in [(0, 34, 49999, 9, 'Yes'), (1, 34, 49999, 9, 'No'), (2, 35, 50000, 10, 'No')]
        ])
        self.source, self.fact, self.dims = build_reference(frame, self.spec)

    def test_dimension_keys_are_unambiguous_and_stable(self):
        self.assertEqual(dimension_key('a', ['b', 'c']), dimension_key('a', ['b', 'c']))
        self.assertNotEqual(dimension_key('a', ['b|c', 'd']), dimension_key('a', ['b', 'c|d']))
        self.assertNotEqual(dimension_key('a', ['b']), dimension_key('b', ['a']))
        for value in [None, 1]:
            with self.assertRaises(ValueError): dimension_key('a', [value])

    def test_lossless_join_and_band_sort(self):
        validate_reference(self.source, self.fact, self.dims)
        self.assertEqual(len(self.dims['dim_demographics']), 2)
        self.assertEqual(self.dims['dim_demographics'].set_index('age_band').age_band_sort.to_dict(), {'Under 35': 1, '35-44': 2})
        self.assertEqual(self.dims['dim_income'].set_index('income_band').income_band_sort.to_dict(), {'Under 50k': 1, '50k-<75k': 2})

    def test_orphan_duplicate_and_attribute_corruption_rejected(self):
        for mutation in ['orphan', 'duplicate_dimension', 'duplicate_fact', 'wrong_attribute', 'wrong_target']:
            fact, dims = self.fact.copy(), {k: v.copy() for k, v in self.dims.items()}
            if mutation == 'orphan': fact.loc[0, 'income_key'] = 'missing'
            if mutation == 'duplicate_dimension': dims['dim_income'] = pd.concat([dims['dim_income'], dims['dim_income'].iloc[[0]]])
            if mutation == 'duplicate_fact': fact = pd.concat([fact, fact.iloc[[0]]])
            if mutation == 'wrong_attribute': dims['dim_demographics'].loc[:, 'Gender'] = 'corrupted'
            if mutation == 'wrong_target': fact.loc[0, 'will_buy_ev_flag'] = 0
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_reference(self.source, fact, dims)

    def test_sql_joins_and_weighted_rate(self):
        names = {r: r for r in [FACT_ROLE, *self.dims]}
        queries = star_queries(names, DIMENSIONS, ['age_band'])
        with sqlite3.connect(':memory:') as db:
            db.row_factory = sqlite3.Row
            self.fact.to_sql(FACT_ROLE, db, index=False)
            for name, frame in self.dims.items(): frame.to_sql(name, db, index=False)
            kpi = dict(db.execute(queries['kpi']).fetchone())
            rows = [dict(r) for r in db.execute(queries['segments'])]
        self.assertAlmostEqual(kpi['purchase_intent_rate'], 1/3)
        self.assertNotAlmostEqual(kpi['purchase_intent_rate'], sum(r['purchase_intent_rate'] for r in rows)/2)
        expected = dict(respondent_count=3, yes_count=1, no_count=2, purchase_intent_rate=1/3, segments=rows)
        check_sql_results(kpi, rows, expected)
        bad = copy.deepcopy(rows)
        bad[0]['no_count'] += 1
        with self.assertRaises(ValueError): check_sql_results(kpi, bad, expected)

    def test_sql_rejects_injected_names(self):
        names = {r: r for r in [FACT_ROLE, *self.dims]}
        names[FACT_ROLE] = 'fact; DROP TABLE x'
        with self.assertRaises(ValueError): star_queries(names, DIMENSIONS, ['age_band'])

    def test_publication_requires_all_star_tables_and_validation(self):
        marker = json.loads((ROOT / 'metadata/gold_published_run.json').read_text())
        marker.update(gold_schema_version=2, dimension_rows={d['role']: 2 for d in DIMENSIONS},
                      star_validation={'status': 'passed'}, sql_validation={'status': 'passed'})
        for role, count in marker['dimension_rows'].items():
            marker['tables'].append({'role': role, 'table': role+'_'+marker['run_id'].lower(), 'rows': count})
        require_publication(marker, 'gold', marker['run_id'], silver_run_id=marker['silver_run_id'])
        for mutation in ['missing_table', 'missing_validation', 'negative_count', 'unknown_version']:
            bad = copy.deepcopy(marker)
            if mutation == 'missing_table': bad['tables'].pop()
            if mutation == 'missing_validation': bad['sql_validation'] = {}
            if mutation == 'negative_count': bad['dimension_rows']['dim_income'] = -1
            if mutation == 'unknown_version': bad['gold_schema_version'] = 3
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                require_publication(bad, 'gold', bad['run_id'], silver_run_id=bad['silver_run_id'])

    def test_binding_rejects_legacy_and_mixed_snapshots(self):
        audit = json.loads((ROOT / 'metadata/e2e_verified_run.json').read_text())
        with self.assertRaises(ValueError): binding_request(audit, 'offline')
        expected = json.loads((ROOT / 'metadata/star_expected_metrics.json').read_text())
        audit.update(gold_schema_version=2, star_validation={'status': 'passed', 'dimension_rows': expected['dimension_rows']}, sql_validation={'status': 'passed'})
        audit['tables'] += [{'role': role, 'table': role+'_'+audit['gold_run_id'].lower(), 'rows': n} for role,n in expected['dimension_rows'].items()]
        request, _ = binding_request(audit, 'offline')
        self.assertEqual(len(request['request']['definitions']), 6)
        self.assertTrue(all(d['schemaName'] == '' for d in request['request']['definitions']))
        audit['tables'][-1]['table'] = 'dim_attitude_incentive_old_snapshot'
        with self.assertRaises(ValueError): binding_request(audit, 'offline')


if __name__ == '__main__':
    unittest.main()
