"""Regenerate portfolio narrative and acceptance targets from computed evidence."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd


def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value.strip()+'\n',encoding='utf-8')


def build_reports(root: Path):
    k = json.loads((root/'reports/kpis.json').read_text(encoding='utf-8'))
    q = json.loads((root/'reports/data_quality.json').read_text(encoding='utf-8'))
    manifest = json.loads((root/'reports/run_manifest.json').read_text(encoding='utf-8'))
    status_path=root/'reports/portfolio_status.json'
    status=json.loads(status_path.read_text(encoding='utf-8')) if status_path.exists() else {}
    desktop_verified=(status.get('power_bi_desktop_validated',False) and status.get('source_sha256')==manifest['source_sha256'])
    services = pd.read_csv(root/'reports/tables/02_service_performance.csv')
    monthly = pd.read_csv(root/'reports/tables/03_monthly_intake.csv')
    backlog = pd.read_csv(root/'reports/tables/04_open_backlog.csv')
    duplicate = pd.read_csv(root/'reports/tables/09_duplicate_mix.csv')
    diagnostics = pd.read_csv(root/'reports/tables/08_workflow_diagnostics.csv')
    service = services.set_index('service_description')
    signal = service.loc['TPW - Traffic Signal - Maintenance']
    striping = service.loc['TPW - Road Markings/Striping - Maintenance']
    signs = service.loc['TPW - Traffic Sign New']
    primary = int(k['primary_requests'])
    duplicate_share = k['business_duplicates']/(k['cohort_rows']-k['test_records'])
    cluster = int(backlog['created_local'].str.slice(0,10).between('2025-05-01','2025-05-05').sum())
    signal_duplicates = duplicate.set_index('service_description').loc['TPW - Traffic Signal - Maintenance']
    missing = pd.read_csv(root/'reports/tables/missingness.csv')
    hours = k['median_closure_days']*24
    by_deadline = int(round(k['closed_by_recorded_deadline_share']*k['deadline_eligible_closed']))
    created_peak = monthly.loc[monthly['requests'].idxmax()]
    snapshot_date = manifest['age_cutoff_local'][:10]

    findings = f'''# Austin 311 Service Operations — findings and recommendations

**Population:** requests created in calendar 2025 and published in the user's November 7, 2026 export of dataset `38mr-dwji`. **Primary cohort:** nonduplicate, nontesting requests. **Age cutoff:** {manifest['age_cutoff_local']}.

## What the evidence establishes

| Measure | Observed result | Eligible population |
| --- | --- | --- |
| Gross 2025 intake | {k['cohort_rows']:,} | All 2025-created records |
| Duplicate-marked intake | {k['business_duplicates']:,} ({duplicate_share:.2%}) | All nontesting intake |
| Testing record | {k['test_records']:,} | Retained, excluded from primary |
| Primary requests | {primary:,} | Nonduplicate, nontesting |
| Reported closed | {k['closed_requests']:,} | Primary |
| Reported open | {k['open_backlog']:,} | Primary, observed statuses |
| Snapshot closure share | {k['snapshot_closure_share']:.3%} | Closed / primary |
| Median administrative closure | {hours:.2f} hours ({k['median_closure_days']:.3f} days) | {int(k['duration_eligible_closed']):,} eligible closed |
| P90 administrative closure | {k['p90_closure_days']:.2f} days | Same eligible closed set |
| Mean administrative closure | {k['mean_closure_days']:.2f} days | Same eligible closed set |
| Closed by recorded deadline | {by_deadline:,} / {int(k['deadline_eligible_closed']):,} ({k['closed_by_recorded_deadline_share']:.2%}) | Valid closed intervals and recorded deadlines |
| Verified resolutions | Unavailable | No verification/outcome field |

The {k['snapshot_closure_share']:.3%} figure describes a mature cohort after substantial follow-up. It does not prove that physical issues were fixed or measure the department's closure performance during calendar 2025. Four primary closed requests have ambiguous Central Time creation timestamps and remain in the closed count while being excluded from elapsed-time metrics.

## 1. Verify the reported backlog before assigning recovery work

All {k['open_backlog']} primary requests still marked Open are past their recorded deadline. Their ages at the fixed cutoff range from {backlog['open_age_days'].min():.1f} to {backlog['open_age_days'].max():.1f} days. {cluster} of {len(backlog)} were created on May 1–5, 2025; all show last-update dates no later than May 2025. Two conflict with the source open flag. The clustering and old update dates suggest checking publication or workflow history; the export alone cannot establish a system defect or confirm that the underlying work is unfinished.

**Proposed action:** the operations/data owner reviews these {len(backlog)} IDs against the live request system and any linked work orders. Record whether each is genuinely open, already completed, transferred or incorrectly published. Fix confirmed status/flag issues through the normal source-system process. Measure verified backlog and reconciliation exceptions afterward. Do not claim an achieved backlog reduction.

Evidence: `04_open_backlog.csv`, `06_quality_checks.csv`, and `quality_issues.csv`.

## 2. Investigate long closure intervals within comparable services

Road Markings/Striping — Maintenance has {int(striping['requests']):,} primary requests, median {striping['median_closure_days']:.2f} days and P90 {striping['p90_closure_days']:.2f} days. Traffic Sign New has {int(signs['requests']):,} requests, median {signs['median_closure_days']:.2f} days and P90 {signs['p90_closure_days']:.2f} days. Yet striping's recorded-deadline closure share is {striping['closed_by_recorded_deadline_share']:.2%}; a long duration alone is not evidence of a missed target. Sign New's corresponding share is {signs['closed_by_recorded_deadline_share']:.2%}.

**Proposed action:** service managers sample long-duration cases and compare planning, inspection, batching, material availability and target-setting rules. These are candidate explanations, not observed causes. Establish service-specific baselines before testing a scheduling change. Track eligible N, median/P90 and recorded-deadline share together. No staffing increase, savings estimate or causal claim is supported by the current file.

Evidence: `02_service_performance.csv` and `08_workflow_diagnostics.csv`.

## 3. Treat duplicate-marked requests as a separate demand signal

There are {k['business_duplicates']:,} duplicate-marked requests, {duplicate_share:.2%} of nontesting intake. Traffic Signal — Maintenance accounts for {int(signal_duplicates['duplicate_marked']):,} of them out of {int(signal_duplicates['total_intake']):,} total signal-maintenance reports ({signal_duplicates['duplicate_marked_share']:.2%}). Its primary count is {int(signal['requests']):,}. A report is not necessarily an independent incident, and the data lacks a parent-request key to reconstruct incident groups.

**Proposed action:** inspect a sample of duplicate signal reports to understand whether repeated reporting, routing practices or another process explains the designation. Consider clearer resident status updates only if that review supports the idea. Preserve the additional reports as a demand indicator rather than deleting them or promising a preventable workload reduction.

Evidence: `05_duplicate_sensitivity.csv` and `09_duplicate_mix.csv`.

## 4. Separate administrative workflows from field-service claims

Lane/Road Closure Notification has {int(service.loc['TPW - Lane/Road Closure Notification','requests']):,} primary requests and both median and P90 equal to zero elapsed days. Activate/Deactivate Work Zone has {int(service.loc['TPW - Activate/Deactivate Work Zone','requests']):,} and the same pattern. These are timestamp observations, not proof of instantaneous field work. The all-service median also reflects the volume of fast parking and signal workflows.

**Proposed action:** agree with service owners which request types represent notifications, triage, investigation and repair. Create a verified workflow crosswalk in a later version. Publish closure metrics under their actual meaning, and add work-order completion/inspection evidence before introducing a verified resolution KPI.

Evidence: `08_workflow_diagnostics.csv` and the official field definitions.

## Demand context and limits

The highest primary intake month is {created_peak['year_month']} with {int(created_peak['requests']):,} requests. One year is insufficient to establish recurring seasonality. Channel and service mix, differing targets and unequal follow-up complicate comparisons. This snapshot does not establish historical month-end backlog, capacity, all-years TPW backlog, costs or service equity. All recommendations above are proposals; none has been implemented or evaluated in this project.
'''
    write(root/'reports/findings.md',findings)

    quality_report = f'''# Data quality assessment

The full downloaded file contains **{q['source_rows']:,} rows** across 25 columns. The calendar-2025 cohort contains **{q['cohort_rows']:,} rows**; {q['outside_2025']:,} are outside scope. Cohort creation dates range from {q['created_date_range_local'][0]} to {q['created_date_range_local'][1]} Central Time.

| Check | Observed result | Treatment |
| --- | --- | --- |
| Missing or repeated request IDs | 0 | Mandatory key; fail on future violations |
| Exact repeated rows in cohort | 0 | Distinct from business duplicate flag |
| Business duplicate-marked requests | {q['business_duplicate_requests']:,} | Retain; separate from primary KPIs |
| Testing requests | {q['test_requests']} | Retain; exclude from primary KPIs |
| Unparseable populated timestamps | {sum(q['invalid_date_values'].values())} | Do not impute; report and exclude affected intervals |
| Ambiguous/nonexistent local timestamps | {q['timestamp_affected_requests']} requests | Preserve counts; exclude ambiguous elapsed durations |
| Status/open-flag conflicts | {q['status_flag_conflicts']} | Status mapping takes precedence; preserve source flags |
| Source overdue-flag disagreements at fixed cutoff, gross intake | {q['open_overdue_flag_conflicts']} | Derive open-past-deadline from usable timestamps |
| Source open-age differences greater than one day, gross intake | {q['source_open_age_conflicts_over_one_day']} | Use the fixed-cutoff elapsed age, preserve source age |
| Negative closure intervals | {q['negative_closure_intervals']} | Exclude invalid durations; do not substitute zero |
| Recorded deadlines before creation | {q['deadline_before_creation']} | Exclude from deadline-based eligibility |
| Computed-vs-source on-time conflicts among eligible closed | {q['deadline_flag_conflicts']} | Calculate from timestamps; do not assume a generic deadline |
| Missing close dates | 19 | All belong to records with an open status, including one duplicate |
| Missing location/coordinates | 378 each ({378/q['cohort_rows']:.3%}) | Leave null; disclose map coverage |
| Service-description cells trimmed | {q['trimmed_cells']['Service Request Description']:,} | Remove surrounding whitespace only |
| Address cells trimmed | {q['trimmed_cells']['Service Request Location']:,} | Remove surrounding whitespace only |

The status distribution is {q['status_counts']}. The source flags count 17 open records in gross intake, while explicit open statuses identify 19; excluding the one duplicate-open record gives 18 primary open records. The two disagreements are requests `25-00078025` and `25-00140032`.

All 19 gross-intake open records have published age values inconsistent with the fixed snapshot cutoff by more than one day. The two flag-conflict records, for example, have published age values of 3 and 5 days despite creation dates in March and May 2025. The source age is not used as a headline age measure. The cleaned table preserves it; `open_age_days` is calculated from timestamps and the declared cutoff. Published `Response Days` is retained but cannot independently establish first-response time because no matching event timestamp is provided.

Missingness is assessed before any imputation (none is performed). The full field-by-field missingness table is `tables/missingness.csv`; row-level exceptions are `tables/quality_issues.csv`. Raw values are retained in the SQLite table `raw_requests_2025` and the frozen full source file. Source age/response fields and all source flags remain recoverable.

The warehouse passes SQLite integrity and foreign-key checks. Python group medians/P90 values agree with independently implemented SQL continuous percentiles to 1e-10 days. Monthly creation counts and closure-month counts reconcile to their respective primary totals. Synthetic tests exercise calendar-year boundaries, daylight saving, ambiguous times, business duplicates, testing records, negative intervals and source-flag disagreements.

Power BI Desktop validation remains pending; see `docs/desktop_validation.md`. Data quality does not establish real-world work completion.
'''
    if desktop_verified:
        quality_report=quality_report.replace('Power BI Desktop validation remains pending;', 'Power BI Desktop measures, filters and date roles have been validated against this snapshot;')
    write(root/'reports/data_quality.md',quality_report)
    metadata = json.loads((root/'data/raw/city_metadata.json').read_text(encoding='utf-8'))
    pd.DataFrame([{'export_column':c['name'],'api_field':c['fieldName'],'socrata_type':c['dataTypeName']}
                  for c in metadata['columns'] if not c['fieldName'].startswith(':')]).to_csv(root/'docs/source_fields.csv',index=False)

    top_rows = '\n'.join(f"| {r.service_description.removeprefix('TPW - ')} | {r.requests:,} | {r.median_closure_days:.2f} | {r.p90_closure_days:.2f} |" for r in services.head(6).itertuples())
    readme = fr'''# Austin 311 Service Operations Analytics

**Python · SQL · Power BI model design · Public-service operations**

**v0.1 — Private working version.** Python/SQL analysis is validated. Power BI Desktop implementation and public portfolio release are pending.

An analysis of 2025-created Transportation and Public Works service requests: reported demand, administrative closure intervals, recorded deadlines and the reported open backlog visible in a November 7, 2026 export.

![Static analytical preview; not a Power BI screenshot](reports/dashboard_preview.png)

The business question is how managers can identify workload patterns and service types that deserve closer review. This project emphasizes defensible definitions, reproducibility and operational recommendations supported by the published data.

## Key results

- **{k['cohort_rows']:,}** gross requests created in 2025; **{primary:,}** in the nonduplicate, nontesting primary cohort.
- **{k['closed_requests']:,}** primary requests marked closed; **{k['open_backlog']}** still marked open in the export.
- Median closure time **{hours:.2f} hours** and P90 **{k['p90_closure_days']:.2f} days**, among **{int(k['duration_eligible_closed']):,}** eligible closed requests.
- **{cluster} of {len(backlog)}** primary open records were created on May 1–5, 2025; all have old update dates. Verify their current status before treating them as confirmed unfinished work.
- **{q['status_flag_conflicts']}** status/open-flag conflicts and **{q['timestamp_affected_requests']}** ambiguous creation timestamps are explicitly handled.

**Closed is an administrative status. Verified resolution is unavailable.** The snapshot closure share is {k['snapshot_closure_share']:.3%}, measured after substantial follow-up. It is not a 2025 annual closure rate or a verified repair success rate. The reported backlog covers only requests created in 2025, not all departmental work.

| Primary service type | Requests | Median days | P90 days |
| --- | ---: | ---: | ---: |
{top_rows}

Findings and proposals: [recommendations report](reports/findings.md). Definitions and tradeoffs: [methodology](docs/methodology.md). Field-level exceptions: [quality assessment](reports/data_quality.md).

## Reproduce the analysis

Use Python 3.12. From the project root:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python src/pipeline.py
.venv\Scripts\python -m unittest discover -s tests -v
```

The complete local delivery includes `data/raw/source_snapshot.csv` and its official metadata. The original source is unchanged. The pipeline runs offline, selects calendar 2025 by creation timestamp, writes a clean CSV and SQLite warehouse, exports BI tables, executes the SQL analyses and regenerates the reports and preview. The default fixed age cutoff is {snapshot_date} midnight Central Time.

**If you cloned the GitHub repository:** the large source CSV is intentionally excluded. Place the matching official export at `data/raw/source_snapshot.csv` before running the pipeline, or use the downloader below to acquire a new snapshot. Synthetic tests require only the included metadata and can run without the full export. A new live export may produce different results; use the saved source hash to identify the frozen v1 input.

For a separately acquired input:

```powershell
python src/pipeline.py --input "C:\path\to\official_export.csv" --metadata "C:\path\to\city_metadata.json" --asof 2026-11-07
```

`--asof` must follow the cohort's observed close/update/status-change timestamps. It does not reconstruct earlier states. Do not use an old cutoff with a new live export. The run manifest stores input and metadata hashes, row counts, tool versions and reconciliation results. No credentials or database server are required.

To download a **new** official snapshot into a new folder:

```powershell
python src/download_source.py --destination data/raw/refresh_2026-11-08
```

This uses the full CSV export endpoint to avoid silent API default row limits. Metadata and CSV are separate live requests; they are not an atomic transaction. New data can change historical request statuses and therefore the results. The saved v1 file is the reproducibility source, not today's portal response.

## Repository contents

| Path | Purpose |
| --- | --- |
| `src/pipeline.py` | Validation, typed cleaning, time-zone handling, warehouse and BI exports |
| `src/download_source.py` | Optional new full City export and acquisition manifest |
| `src/build_reports.py` | Evidence-driven reports and acceptance values |
| `src/render_preview.py` | Static preview built from computed tables |
| `sql/` | Explicit schema and nine analytical queries |
| `data/processed/` | Clean 2025 request CSV with source and derived fields |
| `data/warehouse/austin_311.sqlite` | Queryable SQLite warehouse with fact, dimensions and raw cohort |
| `data/powerbi/` | One fact, four dimensions and one snapshot CSV |
| `powerbi/` | Power Query, DAX, theme, relationships and dashboard plan |
| `reports/` | Computed tables, JSON evidence, narrative and static preview |
| `docs/` | Methodology, dictionaries, interview guide and review milestones |
| `tests/` | Meaningful synthetic boundary cases |

## Power BI readiness

The fact/dimension exports and [dashboard plan](powerbi/dashboard_plan.md) are ready for Desktop implementation. The package includes import queries, DAX measures, a theme, relationship instructions and expected acceptance values. **No interactive `.pbix` has been built or validated yet.** The preview above is generated directly from validated Python/SQL results. Desktop import, measure execution, filter behavior and a real dashboard screenshot remain a separate milestone.

## Analytical choices

Use Central Time for calendar-year selection and UTC for actual elapsed-time subtraction. Preserve duplicate-marked reports as demand evidence, but exclude them and testing records from primary performance summaries. Resolve two source open-flag disagreements using the explicit status and missing close dates while retaining the original fields. Exclude four ambiguous fall-hour timestamps from durations, not from volumes. Keep organizational label variants separate until a crosswalk is verified. Do not impute dates or geography.

Recommended follow-up: verify the small reported backlog in the live system; review long closure intervals within comparable service types; investigate the concentration of duplicate signal reports; and distinguish administrative closures from verified service outcomes. These are proposals, not measured operational improvements.

## Verification and publication

The build checks IDs, schema, binary flags, timestamps, foreign keys and SQLite integrity. Independently written SQL/Python median and P90 calculations reconcile, as do intake and dated closure-month totals. Eight synthetic tests pass for the v1 build. See [run evidence](reports/run_manifest.json) and [Desktop validation status](docs/desktop_validation.md).

The private repository stores source code, SQL, documentation, aggregate reports, theme and preview. Raw exports, generated row-level tables, request-level exception/backlog CSVs, the database and `.pbix` files are excluded by `.gitignore`. The full source is approximately 163 MB and exceeds GitHub's ordinary single-file limit. For exact public reproduction, arrange a versioned data-release asset and verify redistribution terms first. A fresh live download is analytically reproducible but may not reproduce the frozen snapshot's numbers. Public release remains pending the Power BI and final presentation review.

## Sources and attribution

- [City of Austin dataset — 38mr-dwji](https://data.austintexas.gov/d/38mr-dwji), with [field metadata](https://data.austintexas.gov/api/views/38mr-dwji.json).
- [Federal catalog record](https://catalog.data.gov/dataset/311-service-requests-austin-transportation-and-public-works), confirming department scope and Central Time.
- [City of Austin 311 reporting repository](https://github.com/cityofaustin/dts-311-reporting), providing publisher workflow context.
- Microsoft [star-schema](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema) and [date-table](https://learn.microsoft.com/en-us/power-bi/guidance/model-date-tables) guidance for the proposed semantic model.

The public metadata does not provide a named license identifier in the captured `licenseId` field. Attribute the City and confirm the applicable portal terms before redistributing row-level records. This independent portfolio project is not an official City dashboard.
'''
    if desktop_verified:
        readme=readme.replace('**v0.1 — Private working version.** Python/SQL analysis is validated. Power BI Desktop implementation and public portfolio release are pending.', '**v1.0 — Desktop-validated portfolio version.** Python, SQL and the three-page Power BI report are validated. The repository remains private pending the public-release review.')
        readme=readme.replace('![Static analytical preview; not a Power BI screenshot](reports/dashboard_preview.png)', '![Actual Power BI Desktop report export](reports/dashboard-1.png)')
        old='The fact/dimension exports and [dashboard plan](powerbi/dashboard_plan.md) are ready for Desktop implementation. The package includes import queries, DAX measures, a theme, relationship instructions and expected acceptance values. **No interactive `.pbix` has been built or validated yet.** The preview above is generated directly from validated Python/SQL results. Desktop import, measure execution, filter behavior and a real dashboard screenshot remain a separate milestone.'
        new='The native [Power BI project](powerbi/desktop/A311.pbip) contains three interactive pages: operations overview, service comparisons, and reported backlog/quality. It was opened, refreshed, saved and reopened in Power BI Desktop 2.159.1231.0. Seven read-only DAX query checks reconcile the headline metrics, all 43 service percentiles, service/month filter contexts, date roles and relationship integrity to Python/SQL. Month and service selections, filter clearing and an empty backlog were also checked in the actual report. See [validation evidence](docs/desktop_validation.md) and the [native PDF export](reports/Austin-311-Service-Operations-Dashboard.pdf).\n\nTo open it locally, run the cleaning pipeline, then `python src/build_powerbi_project.py` and open `powerbi/desktop/A311.pbip` in Desktop. Refresh the model. The builder sets the local `pProjectFolder` parameter; the repository copy uses a generic path that must be configured on another computer. Local caches and bulk request data are excluded from Git. The PDF and PNGs show the visible table viewport; use the interactive report to scroll through all rows.'
        readme=readme.replace(old,new)
        readme=readme.replace('Public release remains pending the Power BI and final presentation review.', 'Public release remains pending the final presentation and repository-visibility review.')
        if status.get('public_release',False):
            readme=readme.replace('The repository remains private pending the public-release review.', 'Published as a public portfolio project on November 7, 2026.')
            readme=readme.replace('The private repository stores', 'The public repository stores')
            readme=readme.replace('Public release remains pending the final presentation and repository-visibility review.', 'The reviewed repository and aggregate report artifacts are public.')
            if status.get('linkedin_attached',False):
                readme=readme.replace('The reviewed repository and aggregate report artifacts are public.', 'The reviewed repository and aggregate report artifacts are public. The project is also listed in the Projects and Featured sections of the author\'s LinkedIn profile.')
    write(root/'README.md',readme)

    targets = [
        ('Gross intake',int(k['cohort_rows']),'rows'),
        ('All Nontest Intake',int(k['cohort_rows']-k['test_records']),'rows'),
        ('Primary Requests',primary,'rows'),
        ('Reported Closed Requests',int(k['closed_requests']),'rows'),
        ('Reported Open Backlog',int(k['open_backlog']),'rows'),
        ('Snapshot Closure Share',k['snapshot_closure_share'],'fraction'),
        ('Duration Eligible Closed',int(k['duration_eligible_closed']),'rows'),
        ('Median Closure Days',k['median_closure_days'],'elapsed days'),
        ('Median Closure Hours',hours,'elapsed hours'),
        ('P90 Closure Days',k['p90_closure_days'],'elapsed days'),
        ('Deadline Eligible Closed',int(k['deadline_eligible_closed']),'rows'),
        ('Closed By Recorded Deadline',by_deadline,'rows'),
        ('Closed By Recorded Deadline Share',k['closed_by_recorded_deadline_share'],'fraction'),
        ('Reported Open Past Deadline',int(k['open_past_recorded_deadline']),'rows'),
        ('Duplicate Marked Intake',int(k['business_duplicates']),'rows'),
        ('Duplicate Marked Share',duplicate_share,'fraction'),
        ('Flag Conflicts In Primary',int(q['status_flag_conflicts']),'rows')]
    pd.DataFrame(targets,columns=['measure','expected_unfiltered_value','unit']).to_csv(root/'reports/powerbi_acceptance.csv',index=False)
    with sqlite3.connect(root/'data/warehouse/austin_311.sqlite') as connection:
        fact_schema = pd.read_sql_query('PRAGMA table_info(fact_requests)',connection)
        fact_schema[['name','type','notnull','pk']].to_csv(root/'docs/fact_schema.csv',index=False)
    from render_preview import render_preview
    render_preview(root,k,services,monthly,backlog)


if __name__=='__main__':
    build_reports(Path(__file__).resolve().parents[1])
