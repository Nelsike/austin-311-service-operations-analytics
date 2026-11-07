# Data quality assessment

The full downloaded file contains **376,135 rows** across 25 columns. The calendar-2025 cohort contains **73,690 rows**; 302,445 are outside scope. Cohort creation dates range from 2025-01-01 00:49:37 to 2025-12-31 23:21:48 Central Time.

| Check | Observed result | Treatment |
| --- | --- | --- |
| Missing or repeated request IDs | 0 | Mandatory key; fail on future violations |
| Exact repeated rows in cohort | 0 | Distinct from business duplicate flag |
| Business duplicate-marked requests | 4,540 | Retain; separate from primary KPIs |
| Testing requests | 1 | Retain; exclude from primary KPIs |
| Unparseable populated timestamps | 0 | Do not impute; report and exclude affected intervals |
| Ambiguous/nonexistent local timestamps | 4 requests | Preserve counts; exclude ambiguous elapsed durations |
| Status/open-flag conflicts | 2 | Status mapping takes precedence; preserve source flags |
| Source overdue-flag disagreements at fixed cutoff, gross intake | 17 | Derive open-past-deadline from usable timestamps |
| Source open-age differences greater than one day, gross intake | 19 | Use the fixed-cutoff elapsed age, preserve source age |
| Negative closure intervals | 0 | Exclude invalid durations; do not substitute zero |
| Recorded deadlines before creation | 0 | Exclude from deadline-based eligibility |
| Computed-vs-source on-time conflicts among eligible closed | 0 | Calculate from timestamps; do not assume a generic deadline |
| Missing close dates | 19 | All belong to records with an open status, including one duplicate |
| Missing location/coordinates | 378 each (0.513%) | Leave null; disclose map coverage |
| Service-description cells trimmed | 952 | Remove surrounding whitespace only |
| Address cells trimmed | 385 | Remove surrounding whitespace only |

The status distribution is {'Closed': 69131, 'Duplicate (closed)': 4539, 'Open': 18, 'Duplicate (open)': 1, 'CancelledTesting': 1}. The source flags count 17 open records in gross intake, while explicit open statuses identify 19; excluding the one duplicate-open record gives 18 primary open records. The two disagreements are requests `25-00078025` and `25-00140032`.

All 19 gross-intake open records have published age values inconsistent with the fixed snapshot cutoff by more than one day. The two flag-conflict records, for example, have published age values of 3 and 5 days despite creation dates in March and May 2025. The source age is not used as a headline age measure. The cleaned table preserves it; `open_age_days` is calculated from timestamps and the declared cutoff. Published `Response Days` is retained but cannot independently establish first-response time because no matching event timestamp is provided.

Missingness is assessed before any imputation (none is performed). The full field-by-field missingness table is `tables/missingness.csv`; row-level exceptions are `tables/quality_issues.csv`. Raw values are retained in the SQLite table `raw_requests_2025` and the frozen full source file. Source age/response fields and all source flags remain recoverable.

The warehouse passes SQLite integrity and foreign-key checks. Python group medians/P90 values agree with independently implemented SQL continuous percentiles to 1e-10 days. Monthly creation counts and closure-month counts reconcile to their respective primary totals. Synthetic tests exercise calendar-year boundaries, daylight saving, ambiguous times, business duplicates, testing records, negative intervals and source-flag disagreements.

Power BI Desktop validation remains pending; see `docs/desktop_validation.md`. Data quality does not establish real-world work completion.
