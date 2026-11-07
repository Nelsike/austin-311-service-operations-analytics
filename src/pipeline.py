"""Build the frozen 2025-created request cohort, SQLite warehouse and BI exports.

Run from the project root: python src/pipeline.py
No network access, notebook state, credentials or paid database is required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FORMAT = '%Y %b %d %I:%M:%S %p'
ZONE = 'America/Chicago'
STATUS = {'Closed': 'Closed', 'Duplicate (closed)': 'Closed',
          'Open': 'Open', 'Duplicate (open)': 'Open', 'CancelledTesting': 'Excluded'}
DATE_FIELDS = ['created_date', 'close_date', 'overdue_on_date', 'last_update_date', 'status_change_date']
NUMBER_FIELDS = ['is_duplicate_1_0', 'sr_age_days', 'response_days', 'open_count',
                 'closed_count', 'overdue_count', 'closed_on_time', 'closed_late',
                 'of_days_late', 'fiscal_year', 'state_plane_x_coordinate', 'state_plane_y_coordinate']
BOOLEAN_FIELDS = ['is_duplicate_1_0', 'open_count', 'closed_count', 'overdue_count', 'closed_on_time', 'closed_late']


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def json_write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def date_key(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.dt.strftime('%Y%m%d'), errors='coerce').astype('Int64')


def local_text(series: pd.Series) -> pd.Series:
    return series.dt.strftime('%Y-%m-%dT%H:%M:%S').astype('string')


def utc_text(series: pd.Series) -> pd.Series:
    return series.dt.strftime('%Y-%m-%dT%H:%M:%SZ').astype('string')


def dimension(data: pd.DataFrame, columns: list[str], key: str) -> pd.DataFrame:
    values = data[columns].drop_duplicates().sort_values(columns).reset_index(drop=True)
    values.insert(0, key, range(1, len(values) + 1))
    return values


def prepare(source: Path, asof: str, metadata: dict):
    columns = [c for c in metadata['columns'] if not c['fieldName'].startswith(':')]
    mapping = {c['name']: c['fieldName'] for c in columns}
    original = pd.read_csv(source, dtype='string', keep_default_na=False)
    if set(original.columns) != set(mapping):
        raise ValueError('CSV schema differs from frozen official metadata; inspect before proceeding.')
    trimmed = original.apply(lambda s: s.str.strip())
    all_created = pd.to_datetime(trimmed['Created Date'], format=FORMAT, errors='coerce')
    if all_created.isna().any():
        raise ValueError('Invalid/missing created dates prevent a complete 2025 selection.')
    mask = all_created.ge('2025-01-01') & all_created.lt('2026-01-01')
    raw = original.loc[mask].copy().reset_index(drop=True)
    if raw.empty:
        raise ValueError('No records created in calendar 2025.')
    clean = trimmed.loc[mask].rename(columns=mapping).reset_index(drop=True)
    if clean['service_request_sr_number'].eq('').any() or clean['service_request_sr_number'].duplicated().any():
        raise ValueError('Missing/duplicate request IDs: quarantine and review; never silently discard.')
    missing = pd.DataFrame([
        {'field': c, 'missing_count': int(raw[c].str.strip().eq('').sum()),
         'missing_pct': float(raw[c].str.strip().eq('').mean() * 100)} for c in raw
    ])
    local, utc, errors, ambiguous = {}, {}, {}, {}
    for field in DATE_FIELDS:
        local[field] = pd.to_datetime(clean[field], format=FORMAT, errors='coerce')
        errors[field] = int((clean[field].ne('') & local[field].isna()).sum())
        localized = local[field].dt.tz_localize(ZONE, ambiguous='NaT', nonexistent='NaT')
        utc[field] = localized.dt.tz_convert('UTC')
        ambiguous[field] = local[field].notna() & localized.isna()
    numeric = {}
    for field in NUMBER_FIELDS:
        numeric[field] = pd.to_numeric(clean[field].str.replace(',', '', regex=False), errors='coerce')
        if (clean[field].ne('') & numeric[field].isna()).any():
            raise ValueError(f'Unparseable numeric field: {field}')
    for field in BOOLEAN_FIELDS:
        if not numeric[field].isin([0, 1]).all():
            raise ValueError(f'Nonbinary/missing flag: {field}')
    cutoff = pd.Timestamp(asof)
    if cutoff.tzinfo is not None:
        raise ValueError('--asof must be a local calendar date, such as 2026-11-07.')
    cutoff = cutoff.tz_localize(ZONE).tz_convert('UTC')
    if local['created_date'].ge(pd.Timestamp(asof)).any():
        raise ValueError('Age cutoff must follow all cohort creation dates.')
    for field in ['close_date','last_update_date','status_change_date']:
        if utc[field].gt(cutoff).any():
            raise ValueError(f'{field} occurs after age cutoff; do not mislabel snapshot state.')

    f = pd.DataFrame({'request_number': clean['service_request_sr_number']})
    f['source_status'] = clean['sr_status']
    f['status_class'] = clean['sr_status'].map(STATUS).fillna('Unknown')
    f['is_business_duplicate'] = numeric['is_duplicate_1_0'].astype(int)
    f['is_test'] = clean['sr_status'].eq('CancelledTesting').astype(int)
    f['in_primary'] = ((f['is_business_duplicate'] == 0) & (f['is_test'] == 0)).astype(int)
    f['is_closed'] = f['status_class'].eq('Closed').astype(int)
    f['is_open'] = f['status_class'].eq('Open').astype(int)
    f['created_date_key'] = date_key(local['created_date'])
    f['closed_date_key'] = date_key(local['close_date'])
    f['deadline_date_key'] = date_key(local['overdue_on_date'])
    for field, prefix in [('created_date','created'), ('close_date','closed'), ('overdue_on_date','deadline')]:
        f[f'{prefix}_local'] = local_text(local[field])
        f[f'{prefix}_utc'] = utc_text(utc[field])
    f['last_updated_local'] = local_text(local['last_update_date'])
    elapsed = (utc['close_date'] - utc['created_date']).dt.total_seconds() / 86400
    valid = f['is_closed'].eq(1) & elapsed.ge(0) & utc['close_date'].le(cutoff)
    f['valid_closure'] = valid.astype(int)
    f['closure_days'] = elapsed.where(valid)
    valid_deadline = valid & utc['overdue_on_date'].notna() & utc['overdue_on_date'].ge(utc['created_date'])
    f['valid_deadline_closure'] = valid_deadline.astype(int)
    f['closed_by_deadline'] = pd.Series(pd.NA,index=f.index,dtype='Int64')
    f.loc[valid_deadline,'closed_by_deadline'] = utc['close_date'].le(utc['overdue_on_date'])[valid_deadline].astype(int)
    f['open_age_days'] = ((cutoff - utc['created_date']).dt.total_seconds()/86400).where(f['is_open'].eq(1))
    f['open_past_deadline'] = pd.Series(pd.NA,index=f.index,dtype='Int64')
    open_due = f['is_open'].eq(1) & utc['overdue_on_date'].notna() & utc['overdue_on_date'].ge(utc['created_date'])
    f.loc[open_due,'open_past_deadline'] = utc['overdue_on_date'].lt(cutoff)[open_due].astype(int)
    for target, field in [('source_is_open','open_count'), ('source_is_closed','closed_count'),
                          ('source_is_overdue','overdue_count'), ('source_closed_on_time','closed_on_time'),
                          ('source_response_days','response_days'), ('source_age_days','sr_age_days'),
                          ('source_fiscal_year','fiscal_year')]:
        f[target] = numeric[field]
    known = f['status_class'].isin(['Closed','Open'])
    f['status_flag_conflict'] = (known & (f['is_open'].ne(f['source_is_open']) | f['is_closed'].ne(f['source_is_closed']))).astype(int)
    f['deadline_flag_conflict'] = (valid_deadline & f['closed_by_deadline'].ne(f['source_closed_on_time']).fillna(False)).astype(int)
    f['timestamp_ambiguity'] = pd.DataFrame(ambiguous).any(axis=1).astype(int)
    point = clean['location'].str.extract(r'^POINT\s*\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)$')
    f['longitude'] = pd.to_numeric(point[0], errors='coerce')
    f['latitude'] = pd.to_numeric(point[1], errors='coerce')
    bad_geo = f['longitude'].notna() & (~f['longitude'].between(-180,180) | ~f['latitude'].between(-90,90))
    if bad_geo.any():
        raise ValueError('Out-of-range coordinates; inspect source CRS.')
    ds = dimension(clean.rename(columns={'sr_description':'service_description'}), ['service_description'], 'service_key')
    do = dimension(clean, ['department','group_description'], 'organization_key')
    dc = dimension(clean, ['method_received'], 'channel_key')
    enriched = clean.rename(columns={'sr_description':'service_description'}).merge(ds,on='service_description',validate='many_to_one').merge(do,on=['department','group_description'],validate='many_to_one').merge(dc,on='method_received',validate='many_to_one')
    lookup = enriched.set_index('service_request_sr_number')
    for key in ['service_key','organization_key','channel_key']:
        f[key] = f['request_number'].map(lookup[key]).astype(int)
    endyear = max(pd.Timestamp(asof).year,local['overdue_on_date'].max().year,local['close_date'].max().year)
    dates = pd.Series(pd.date_range('2025-01-01',f'{endyear}-12-31',freq='D'))
    dd = pd.DataFrame({'date_key':date_key(dates),'date':dates.dt.strftime('%Y-%m-%d'),
        'year':dates.dt.year,'quarter':dates.dt.quarter,'month':dates.dt.month,
        'month_name':dates.dt.strftime('%b'),'year_month':dates.dt.strftime('%Y-%m'),
        'month_sort':dates.dt.year*100+dates.dt.month,'weekday':dates.dt.strftime('%A')})
    clean_export = clean.copy()
    for field in DATE_FIELDS:
        clean_export[field] = local_text(local[field])
    for field in NUMBER_FIELDS:
        clean_export[field] = numeric[field]
    for col in f:
        if col not in clean_export:
            clean_export[col] = f[col]
    issues = []
    def flag(mask, issue):
        for request in f.loc[mask,'request_number']:
            issues.append({'request_number':request,'issue':issue})
    flag(f['status_flag_conflict'].eq(1),'status_flag_conflict')
    flag(f['deadline_flag_conflict'].eq(1),'source_deadline_flag_disagreement')
    flag(f['timestamp_ambiguity'].eq(1),'ambiguous_or_nonexistent_central_timestamp')
    flag(f['is_test'].eq(1),'testing_record_excluded_from_primary')
    flag(f['status_class'].eq('Unknown'),'unknown_status_not_forced_open_or_closed')
    flag(f['is_closed'].eq(1) & local['close_date'].isna(),'closed_without_close_date')
    flag(f['is_open'].eq(1) & local['close_date'].notna(),'open_with_close_date')
    overdue_conflict = f['is_open'].eq(1) & f['open_past_deadline'].notna() & f['open_past_deadline'].ne(f['source_is_overdue']).fillna(False)
    age_conflict = f['is_open'].eq(1) & f['open_age_days'].notna() & (np.floor(f['open_age_days'])-f['source_age_days']).abs().gt(1)
    flag(overdue_conflict,'source_overdue_flag_disagrees_with_fixed_cutoff')
    flag(age_conflict,'source_open_age_differs_by_more_than_one_day')
    flag(elapsed.lt(0),'negative_closure_duration')
    flag(clean['location'].ne('') & f['longitude'].isna(),'unparseable_location_point')
    for field in DATE_FIELDS:
        flag(clean[field].ne('') & local[field].isna(),f'unparseable_{field}')
    duplicate_status = clean['sr_status'].str.startswith('Duplicate')
    flag(duplicate_status.ne(f['is_business_duplicate'].eq(1)),'duplicate_status_flag_conflict')
    quality = {
        'source_rows':len(original),'outside_2025':int((~mask).sum()),'cohort_rows':len(f),
        'created_date_range_local':[str(local['created_date'].min()),str(local['created_date'].max())],
        'all_source_created_range_local':[str(all_created.min()),str(all_created.max())],
        'duplicate_request_ids':int(clean['service_request_sr_number'].duplicated().sum()),
        'exact_duplicate_rows':int(raw.duplicated().sum()),
        'business_duplicate_requests':int(f['is_business_duplicate'].sum()),
        'test_requests':int(f['is_test'].sum()),
        'primary_requests':int(f['in_primary'].sum()),
        'status_flag_conflicts':int(f['status_flag_conflict'].sum()),
        'deadline_flag_conflicts':int(f['deadline_flag_conflict'].sum()),
        'open_overdue_flag_conflicts':int(overdue_conflict.sum()),
        'source_open_age_conflicts_over_one_day':int(age_conflict.sum()),
        'negative_closure_intervals':int(elapsed.lt(0).sum()),
        'deadline_before_creation':int(utc['overdue_on_date'].lt(utc['created_date']).sum()),
        'invalid_date_values':errors,
        'ambiguous_or_nonexistent_timestamps':{k:int(v.sum()) for k,v in ambiguous.items()},
        'timestamp_affected_requests':int(f['timestamp_ambiguity'].sum()),
        'primary_closed_excluded_from_duration':int((f['in_primary'].eq(1) & f['is_closed'].eq(1) & f['valid_closure'].eq(0)).sum()),
        'trimmed_cells':{c:int(original.loc[mask,c].ne(trimmed.loc[mask,c]).sum()) for c in raw},
        'status_counts':clean['sr_status'].value_counts().astype(int).to_dict(),
        'no_verified_resolution_field':True,
    }
    return raw,clean_export,f,{'dim_service':ds,'dim_organization':do,'dim_channel':dc,'dim_date':dd},missing,pd.DataFrame(issues,columns=['request_number','issue']),quality


def make_database(path: Path, f, dimensions, raw, snapshot):
    temporary = path.with_suffix('.building.sqlite')
    if temporary.exists():
        temporary.unlink()
    connection = sqlite3.connect(temporary)
    try:
        connection.executescript((ROOT/'sql/schema.sql').read_text(encoding='utf-8'))
        for table, frame in dimensions.items():
            frame.to_sql(table,connection,if_exists='append',index=False)
        snapshot.to_sql('snapshot',connection,if_exists='append',index=False)
        f.to_sql('fact_requests',connection,if_exists='append',index=False)
        raw.to_sql('raw_requests_2025',connection,if_exists='replace',index=False)
        connection.commit()
        if connection.execute('PRAGMA foreign_key_check').fetchall():
            raise ValueError('Warehouse referential integrity failure.')
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('SQLite integrity failure.')
        for field in ['created_date_key','closed_date_key','deadline_date_key']:
            if connection.execute(f'SELECT COUNT(*) FROM fact_requests f LEFT JOIN dim_date d ON f.{field}=d.date_key WHERE f.{field} IS NOT NULL AND d.date_key IS NULL').fetchone()[0]:
                raise ValueError(f'Orphan dates: {field}')
    finally:
        connection.close()
    temporary.replace(path)


def run(args):
    metadata_path = Path(args.metadata).resolve() if args.metadata else ROOT/'data/raw/city_metadata.json'
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    source = Path(args.input).resolve() if args.input else ROOT/'data/raw/source_snapshot.csv'
    for folder in ['data/processed','data/warehouse','data/powerbi','reports/tables']:
        (ROOT/folder).mkdir(parents=True,exist_ok=True)
    raw,clean,f,dimensions,missing,issues,quality = prepare(source,args.asof,metadata)
    digest = sha256(source)
    local_cutoff = pd.Timestamp(args.asof).tz_localize(ZONE)
    snapshot = pd.DataFrame([{'snapshot_date':args.asof,'age_cutoff_local':local_cutoff.isoformat(),
        'age_cutoff_utc':local_cutoff.tz_convert('UTC').isoformat(),
        'cohort_start':'2025-01-01','cohort_end_exclusive':'2026-01-01','source_file_sha256':digest}])
    db_path = ROOT/'data/warehouse/austin_311.sqlite'
    make_database(db_path,f,dimensions,raw,snapshot)
    clean.to_csv(ROOT/'data/processed/requests_2025_clean.csv',index=False)
    f.to_csv(ROOT/'data/powerbi/fact_requests.csv',index=False)
    for table,frame in dimensions.items():
        frame.to_csv(ROOT/f'data/powerbi/{table}.csv',index=False)
    snapshot.to_csv(ROOT/'data/powerbi/snapshot.csv',index=False)
    missing.to_csv(ROOT/'reports/tables/missingness.csv',index=False)
    issues.to_csv(ROOT/'reports/tables/quality_issues.csv',index=False)
    json_write(ROOT/'reports/data_quality.json',quality)
    with sqlite3.connect(db_path) as connection:
        results = {}
        for sqlfile in sorted((ROOT/'sql').glob('[0-9][0-9]_*.sql')):
            result = pd.read_sql_query(sqlfile.read_text(encoding='utf-8'),connection)
            result.to_csv(ROOT/f'reports/tables/{sqlfile.stem}.csv',index=False)
            results[sqlfile.stem] = result
    primary = f.loc[f['in_primary'].eq(1)]
    durations = primary.loc[primary['valid_closure'].eq(1),'closure_days']
    kpis = results['01_cohort_kpis'].iloc[0].to_dict()
    kpis.update({'median_closure_days':float(durations.median()),'p90_closure_days':float(durations.quantile(.9)),
                'primary_requests':len(primary),'closed_requests':int(primary['is_closed'].sum()),
                'open_backlog':int(primary['is_open'].sum()),
                'cohort_rows':len(f),'business_duplicates':int(f['is_business_duplicate'].sum()),
                'test_records':int(f['is_test'].sum()),'age_cutoff_local':local_cutoff.isoformat()})
    for name,value in list(kpis.items()):
        if isinstance(value,np.generic):
            kpis[name] = value.item()
    # Independent group-level SQL percentile and count reconciliation.
    grouped = primary.groupby('service_key')['closure_days']
    services = results['02_service_performance'].set_index('service_key')
    np.testing.assert_allclose(services['median_closure_days'].sort_index(), grouped.median().sort_index(),rtol=0,atol=1e-10)
    np.testing.assert_allclose(services['p90_closure_days'].sort_index(), grouped.quantile(.9).sort_index(),rtol=0,atol=1e-10)
    if int(results['03_monthly_intake']['requests'].sum()) != len(primary):
        raise ValueError('Monthly intake does not reconcile.')
    if int(primary['is_open'].sum()+primary['is_closed'].sum()) != len(primary):
        raise ValueError('Primary status partition includes unknowns; inspect new statuses.')
    dated_closures = primary['is_closed'].eq(1) & primary['closed_local'].notna()
    if int(results['07_closures_by_month']['cohort_closures'].sum()) != int(dated_closures.sum()):
        raise ValueError('Closure-month counts do not reconcile.')
    json_write(ROOT/'reports/kpis.json',kpis)
    manifest = {'dataset_id':'38mr-dwji','source_url':'https://data.austintexas.gov/d/38mr-dwji',
       'source_filename':source.name,'source_bytes':source.stat().st_size,'source_sha256':digest,
       'metadata_sha256':sha256(metadata_path),'source_rows':quality['source_rows'],
       'cohort_rows':len(f),'age_cutoff_local':local_cutoff.isoformat(),
       'official_metadata_rows_updated_at_utc':pd.Timestamp(metadata['rowsUpdatedAt'],unit='s',tz='UTC').isoformat(),
       'snapshot_note':'Age cutoff is fixed midnight CT. Status is observed in the input export, not reconstructed history. The file observation timestamp is not independently verified.',
       'versions':{'python':__import__('platform').python_version(),'pandas':pd.__version__,'numpy':np.__version__,'sqlite':sqlite3.sqlite_version},
       'validation':{'sql_python_percentiles_match':True,'monthly_intake_reconciles':True,
                     'primary_status_partition_reconciles':True,'closure_month_reconciles':True,
                     'sqlite_integrity_and_foreign_keys_pass':True}}
    json_write(ROOT/'reports/run_manifest.json',manifest)
    from build_reports import build_reports
    build_reports(ROOT)
    print(json.dumps({'kpis':kpis,'quality':quality,'database':str(db_path)},indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',help='Official CSV (default: data/raw/source_snapshot.csv)')
    parser.add_argument('--metadata',help='Matching official metadata JSON (default: frozen metadata)')
    parser.add_argument('--asof',default='2026-11-07',help='Fixed midnight Central Time age cutoff; must follow source updates')
    run(parser.parse_args())
