"""Synthetic boundary cases, separate from the observed City results."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pipeline',ROOT/'src/pipeline.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)
METADATA = json.loads((ROOT/'data/raw/city_metadata.json').read_text(encoding='utf-8'))
MAPPING = {c['fieldName']:c['name'] for c in METADATA['columns'] if not c['fieldName'].startswith(':')}


def row(number='TEST-1', **changes):
    values = {name:'' for name in MAPPING}
    values.update(service_request_sr_number=number,department='Test department',group_description='Test group',
       sr_description='Test service',method_received='Phone',sr_status='Closed',is_duplicate_1_0='0',
       created_date='2025 Mar 08 12:00:00 PM',close_date='2025 Mar 09 12:00:00 PM',
       overdue_on_date='2025 Mar 10 12:00:00 PM',last_update_date='2025 Mar 09 12:00:00 PM',
       status_change_date='2025 Mar 09 12:00:00 PM',sr_age_days='0',response_days='1',open_count='0',
       closed_count='1',overdue_count='0',closed_on_time='1',closed_late='0',of_days_late='0',fiscal_year='2,025')
    values.update(changes)
    return {MAPPING[k]:v for k,v in values.items()}


class PipelineBoundaries(unittest.TestCase):
    def prepare(self,rows):
        scratch = ROOT/'work'
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            Path(folder).resolve().relative_to(scratch.resolve())
            path = Path(folder)/'input.csv'
            pd.DataFrame(rows).to_csv(path,index=False)
            return pipeline.prepare(path,'2026-11-07',METADATA)

    def test_spring_dst_is_23_elapsed_hours(self):
        f = self.prepare([row()])[2]
        self.assertAlmostEqual(f.loc[0,'closure_days'],23/24)

    def test_fall_ambiguous_hour_preserves_volume_excludes_duration(self):
        f = self.prepare([row(created_date='2025 Nov 02 01:30:00 AM',close_date='2025 Nov 03 12:00:00 PM',
            last_update_date='2025 Nov 03 12:00:00 PM',status_change_date='2025 Nov 03 12:00:00 PM',
            overdue_on_date='2025 Nov 04 12:00:00 PM')])[2]
        self.assertEqual(f.loc[0,'in_primary'],1)
        self.assertEqual(f.loc[0,'valid_closure'],0)
        self.assertTrue(pd.isna(f.loc[0,'closure_days']))

    def test_open_status_beats_inconsistent_source_open_flag(self):
        f = self.prepare([row(sr_status='Open',close_date='',closed_count='0')])[2]
        self.assertEqual(f.loc[0,'is_open'],1)
        self.assertEqual(f.loc[0,'status_flag_conflict'],1)
        self.assertEqual(f.loc[0,'open_past_deadline'],1)

    def test_business_duplicate_and_testing_are_preserved_but_not_primary(self):
        f = self.prepare([row('TEST-A',sr_status='Duplicate (closed)',is_duplicate_1_0='1'),
                          row('TEST-B',sr_status='CancelledTesting')])[2]
        self.assertEqual(len(f),2)
        self.assertEqual(int(f['in_primary'].sum()),0)

    def test_calendar_year_boundaries_not_fiscal_year(self):
        f = self.prepare([row('IN',created_date='2025 Dec 31 11:59:59 PM',close_date='2026 Jan 01 12:00:00 PM',
                overdue_on_date='2026 Jan 03 12:00:00 PM',fiscal_year='2,026'),
            row('OUT',created_date='2026 Jan 01 12:00:00 AM')])[2]
        self.assertEqual(f['request_number'].tolist(),['IN'])

    def test_duplicate_ids_fail_instead_of_arbitrary_deduplication(self):
        with self.assertRaisesRegex(ValueError,'duplicate request IDs'):
            self.prepare([row(),row()])

    def test_negative_duration_is_not_zero(self):
        f = self.prepare([row(close_date='2025 Mar 07 12:00:00 PM')])[2]
        self.assertEqual(f.loc[0,'valid_closure'],0)
        self.assertTrue(pd.isna(f.loc[0,'closure_days']))

    def test_closed_without_date_counts_as_closed_but_not_timed(self):
        f = self.prepare([row(close_date='')])[2]
        self.assertEqual(f.loc[0,'is_closed'],1)
        self.assertEqual(f.loc[0,'valid_closure'],0)
        self.assertTrue(pd.isna(f.loc[0,'closure_days']))


if __name__=='__main__':
    unittest.main()
