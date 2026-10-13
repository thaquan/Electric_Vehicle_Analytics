"""Tiny synthetic inputs, never dependent on downloaded/private source data."""
import csv
import json
from pathlib import Path

from scripts.profile_dataset import profile_csv, sha256
from scripts.star_schema import DIMENSIONS


def create_fixture(root):
    raw, meta = root / 'raw', root / 'metadata'
    raw.mkdir(parents=True); meta.mkdir(parents=True)
    common = dict(Age='30', Annual_Income_USD='60000.1234', Daily_Commute_km='20',
                  Number_of_Cars_Owned='1', Charging_Stations_Near_Home='1',
                  Charging_Stations_Near_Work='1', Gender='Female', City_Type='Urban',
                  Current_Car_Type='Petrol', Home_Charging_Possible='Yes',
                  Environmental_Concern_Level='High', Subsidy_Available='Yes', Range_Anxiety_Level='Low')
    datasets = {
        'train.csv': [dict(id=str(i), **common, Will_Buy_EV=label) for i, label in enumerate(('Yes', 'No'))],
        'test.csv': [dict(id='2', **common)],
        'EV_Adoption_and_Range_Anxiety_Dataset.csv': [dict(Buyer_ID='SYNTHETIC_1', **common, Will_Buy_EV='Yes')],
        'sample_submission.csv': [dict(id='2', Will_Buy_EV='Yes')],
    }
    datasets['EV_Adoption_and_Range_Anxiety_Dataset.csv'][0]['Annual_Income_USD'] = ''
    for name, rows in datasets.items():
        with (raw / name).open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    profiles = [profile_csv(p) for p in sorted(raw.glob('*.csv'))]
    spec = json.loads((Path(__file__).resolve().parents[1] / 'metadata/gold_spec.json').read_text())
    spec['segments'] = ['age_band']
    payloads = {
        'source_manifest': {'files': [dict(name=p['file'], bytes=(raw / p['file']).stat().st_size,
            sha256=sha256(raw / p['file']), columns=p['columns'], data_rows=p['data_rows']) for p in profiles]},
        'profiling_summary': profiles,
        'categorical_profile': {p['file']: [c for c in p['column_profiles'] if c['type'] == 'categorical'] for p in profiles},
        'gold_spec': spec,
        'gold_expected_metrics': {'respondent_count': 2, 'yes_count': 1, 'no_count': 1,
            'segments': [{'segment_dimension': 'age_band', 'segment_value': 'Under 35', 'respondent_count': 2, 'yes_count': 1}]},
        'star_expected_metrics': {'dimension_rows': {d['role']: 1 for d in DIMENSIONS}},
    }
    for name, payload in payloads.items():
        (meta / f'{name}.json').write_text(json.dumps(payload), encoding='utf-8')
    return raw, meta
