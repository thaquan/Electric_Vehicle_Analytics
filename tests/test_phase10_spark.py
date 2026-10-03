"""Opt-in tests against real Parquet and Spark: EV_RUN_SPARK_TESTS=1."""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from pyspark.sql import SparkSession, functions as F
from src.gold import build_gold
from src.quality_checks import verify_gold
from scripts.star_schema import DIMENSIONS


@unittest.skipUnless(os.environ.get('EV_RUN_SPARK_TESTS') == '1', 'Set EV_RUN_SPARK_TESTS=1 for real Spark tests')
class Phase10SparkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.spark = (SparkSession.builder.master('local[2]').appName('EV-quality-regression')
                     .config('spark.sql.shuffle.partitions', '2')
                     .config('spark.sql.session.timeZone', 'UTC').getOrCreate())
        cls.spark.sparkContext.setLogLevel('ERROR')
        cls.template = cls.root / 'template/fixture_run'
        cls.meta = cls.root / 'metadata'; cls.meta.mkdir()
        project = Path(__file__).resolve().parents[1]
        spec = json.loads((project / 'metadata/gold_spec.json').read_text())
        spec['segments'] = ['age_band']
        metrics = {'respondent_count': 2, 'yes_count': 1, 'no_count': 1,
                   'segments': [{'segment_dimension': 'age_band', 'segment_value': 'Under 35', 'respondent_count': 2, 'yes_count': 1}]}
        for name, value in [('gold_spec', spec), ('gold_expected_metrics', metrics),
                            ('star_expected_metrics', {'dimension_rows': {d['role']: 1 for d in DIMENSIONS}})]:
            (cls.meta / (name + '.json')).write_text(json.dumps(value))
        frame = cls.spark.range(2).selectExpr(
            'id', 'cast(30 as int) Age', 'cast(60000 as decimal(18,4)) Annual_Income_USD',
            'cast(20 as decimal(18,4)) Daily_Commute_km', 'cast(1 as int) Number_of_Cars_Owned',
            'cast(1 as int) Charging_Stations_Near_Home', 'cast(1 as int) Charging_Stations_Near_Work',
            "'Female' Gender", "'Urban' City_Type", "'Petrol' Current_Car_Type", "'Yes' Home_Charging_Possible",
            "'High' Environmental_Concern_Level", "'Yes' Subsidy_Available", "'Low' Range_Anxiety_Level",
            "case when id=0 then 'Yes' else 'No' end Will_Buy_EV",
            'cast(case when id=0 then 1 else 0 end as int) will_buy_ev_flag',
            "'train' source_dataset", "'train.csv' source_file", "'fixture' source_sha256",
            "cast('2026-10-03 00:00:00' as timestamp) processed_at_utc", "concat('train:', id) record_key")
        frame.write.parquet(str(cls.template / 'silver/train.parquet'))
        build_gold(cls.spark, cls.template / 'silver', cls.meta, cls.template / 'gold', 'fixture_run', 'fixture_run')

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
        cls.tmp.cleanup()

    def setUp(self):
        self.run = self.root / self._testMethodName / 'fixture_run'
        shutil.copytree(self.template, self.run)

    def rewrite(self, role, transform):
        target = self.run / 'gold' / (role + '.parquet')
        scratch = self.run / 'rewrite.parquet'
        transform(self.spark.read.parquet(str(target))).write.parquet(str(scratch))
        shutil.rmtree(target)
        scratch.rename(target)

    def test_valid_full_reconstruction(self):
        result = verify_gold(self.spark, self.run / 'gold', self.meta)
        self.assertEqual(result['tables'], 8)
        self.assertEqual(result['silver_reconstruction'], 'exact')

    def test_corrupt_kpi_rejected(self):
        self.rewrite('agg_ev_kpi', lambda df: df.withColumn('yes_count', F.lit(2).cast('long')))
        with self.assertRaisesRegex(ValueError, 'aggregate'):
            verify_gold(self.spark, self.run / 'gold', self.meta)

    def test_duplicate_segments_rejected(self):
        self.rewrite('agg_ev_segments', lambda df: df.unionByName(df))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            verify_gold(self.spark, self.run / 'gold', self.meta)

    def test_duplicate_fact_id_rejected(self):
        self.rewrite('fact_ev_purchase_intent', lambda df: df.withColumn('id', F.lit(0).cast('long')))
        with self.assertRaisesRegex(ValueError, 'key'):
            verify_gold(self.spark, self.run / 'gold', self.meta)

    def test_changed_dimension_attribute_rejected(self):
        self.rewrite('dim_demographics', lambda df: df.withColumn('Gender', F.lit('changed')))
        with self.assertRaisesRegex(ValueError, 'reconstruction'):
            verify_gold(self.spark, self.run / 'gold', self.meta)

    def test_changed_schema_rejected(self):
        self.rewrite('fact_ev_purchase_intent', lambda df: df.withColumn('id', F.col('id').cast('string')))
        with self.assertRaisesRegex(ValueError, 'schema'):
            verify_gold(self.spark, self.run / 'gold', self.meta)
