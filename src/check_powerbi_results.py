"""Compare actual Desktop DAX query output with independent Python/SQL evidence."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
actual=json.loads((ROOT/'reports/powerbi_actual_results.json').read_text(encoding='utf-8-sig'))
kpis=json.loads((ROOT/'reports/kpis.json').read_text(encoding='utf-8'))
quality=json.loads((ROOT/'reports/data_quality.json').read_text(encoding='utf-8'))
for key,value in actual['headline'][0].items():
    if key in kpis:
        np.testing.assert_allclose(value,kpis[key],atol=1e-10,rtol=0,err_msg=key)
assert actual['headline'][0]['closed_by_deadline']==67120
assert actual['headline'][0]['flag_conflicts']==quality['status_flag_conflicts']
assert actual['headline'][0]['ambiguous_timestamps']==quality['timestamp_affected_requests']
assert actual['headline'][0]['missing_geography_all_intake']==378
assert actual['signal_filter'][0]['requests']==8475
assert actual['signal_filter'][0]['open_backlog']==1
assert actual['may_filter'][0]=={'requests':7062,'open_backlog':16}
assert actual['empty_backlog_filter'][0]['open_backlog']==0
assert actual['empty_backlog_filter'][0]['detail_rows'] in {None,0}
# DAX COUNTROWS returns BLANK for an empty EXCEPT result; that means zero orphans.
assert all(v in {None,0} for v in actual['relationship_orphans'][0].values())
sql=pd.read_csv(ROOT/'reports/tables/02_service_performance.csv').set_index('service_description')
desktop=pd.DataFrame(actual['service_percentiles']).set_index('service_description')
assert set(sql.index)==set(desktop.index)
for source,target in [('requests','requests'),('duration_n','duration_n'),('median_closure_days','median_days'),('p90_closure_days','p90_days')]:
    np.testing.assert_allclose(sql[source].sort_index(),desktop[target].sort_index(),atol=1e-10,rtol=0)
closures=pd.DataFrame(actual['closure_month_role'])
closures=closures[closures['cohort_closures'].fillna(0)>0].set_index('year_month')
sql_closures=pd.read_csv(ROOT/'reports/tables/07_closures_by_month.csv').set_index('closure_month')
assert closures['cohort_closures'].sort_index().to_dict()==sql_closures['cohort_closures'].sort_index().to_dict()
assert int(closures['cohort_closures'].sum())==kpis['closed_requests']
assert any(month.startswith('2026-') for month in closures.index)
checks={'desktop_version':'2.159.1231.0 (October 2026)','queries_executed':len(actual),
    'headline_metrics_match':True,'all_43_service_percentiles_match':True,
    'service_and_month_filter_contexts_match':True,'empty_backlog_handled':True,
    'creation_and_closure_date_roles_match':True,'relationship_orphans':0,
    'method':'Read-only DAX queries against the actual running Power BI Desktop model; compared to saved Python and SQL results.',
    'visual_interaction_review':'Recorded separately in desktop_validation.md'}
(ROOT/'reports/powerbi_validation.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks,indent=2))
