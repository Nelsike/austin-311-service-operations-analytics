# Presenting the project confidently

Use the short explanation first, then open the evidence file relevant to the follow-up. Only claim work and tool use you can demonstrate. In particular, the current delivery prepares the Power BI model and dashboard specification; it does not yet demonstrate a validated interactive Power BI report.

## A 60-second walkthrough

“I analyzed Austin Transportation and Public Works 311 requests created in 2025 to understand reported demand, administrative closure times and the open records visible in a later export. I inspected the actual City definitions before choosing metrics. The download contained multiple years, so I selected the cohort by creation timestamp rather than fiscal year.

“I built a repeatable Python pipeline and a SQLite fact-and-dimension model, then wrote SQL analyses and checked that SQL and Python agreed. I separated duplicate-marked reports from the main performance cohort, retained original values, and handled conflicting flags and daylight-saving ambiguities explicitly.

“The median closure time was about 4.66 hours, but the P90 was about 9.03 days. I recommended service-specific investigation rather than treating every request as comparable. I also found 18 primary requests still marked open, most clustered in early May 2025, and recommended verifying those old records in the live system. My key limitation is that a closed request does not independently verify the physical issue was resolved.”

The quoted explanation describes v1; use the generated results when the data changes. Add that the Power BI import package is ready and show a finished Desktop report only after completing its validation checklist.

## Decisions an interviewer may challenge

| Question | Defensible explanation | Evidence to open |
| --- | --- | --- |
| Why this dataset? | It represents a focused operational domain with public provenance, request-level timestamps and service types; it complements predictive-model projects with SQL and BI work. | README and source dictionary |
| Why 2025? | A complete calendar-year intake cohort gives a manageable, consistent question. Later closures remain part of that cohort. | Creation filter in pipeline.py |
| Why exclude duplicates? | I retained them as demand evidence but excluded business duplicate flags from primary performance comparisons. They are not repeated database IDs, and I cannot reconstruct unique incidents without a parent key. | 05 and 09 SQL results |
| What did you clean? | Exact-format dates, whitespace and comma-formatted numerics; source-status conflicts; time-zone localization; explicit missingness. I did not fill in unavailable dates or geography. | Quality report and raw/clean comparison |
| Why status over flags? | Two records explicitly say Open, lack a close date and have an open flag of zero. I preserve and flag the discrepancy instead of hiding it or discarding those requests. | Request IDs 25-00078025 and 25-00140032 |
| Why UTC subtraction? | The City gives Central Time. Actual elapsed hours across daylight saving differ from simple local-clock subtraction. Four creation times in the fall repeated hour cannot be uniquely interpreted, so I exclude their durations but retain their counts. | Boundary tests and quality issues |
| Why median and P90? | Closure times are skewed. Median describes a typical eligible closed request; P90 shows the slower tail. Neither includes the ongoing duration of still-open requests. | Service performance table |
| Is 99.974% a strong performance result? | It is a snapshot closure share for a mature cohort, with substantial follow-up. It is not a verified resolution rate or a measure of closures performed during 2025. | Methodology and cohort KPIs |
| Does 18 mean the whole department has only 18 open requests? | No. It is the reported primary backlog among requests created in 2025 in this specific dataset and export. Other years and other departments are outside scope. | Backlog SQL filter |
| Why not draw historical backlog? | Current statuses and latest dates do not provide full reopen/transfer history. A history chart would require event data or repeated snapshots. | Methodology limits |
| Did you find a bottleneck? | I found service categories with long administrative closure intervals. The file does not establish whether staffing, batching, inspection or another mechanism caused them. | Findings recommendation 2 |
| Is recorded-deadline share an SLA metric? | I label it as recorded-deadline performance because deadline history, formal service policy and actual resolution evidence are absent. | Deadline calculation and dictionary |
| How did you validate the work? | ID/schema checks, explicit flags, date and database integrity checks, independent SQL/Python percentile agreement, reconciled totals and meaningful synthetic edge cases. | Run manifest and tests |
| What have you done in Power BI? | Prepared typed fact/dimension exports, DAX, Power Query, relationships and a dashboard specification. Desktop execution and interaction checks are a documented remaining milestone. | dashboard_plan.md and desktop_validation.md |
| What business impact did it have? | It is a portfolio analysis with proposed follow-ups. I did not implement an intervention or measure savings or improved service. | Findings report |

## Explain one SQL query without memorizing it

Start with `01_cohort_kpis.sql`. `v_primary_requests` enforces the main population once. `COUNT(*)` counts requests, while `SUM(is_closed)` and `SUM(is_open)` count indicator values. Multiplying by `1.0` makes a fraction rather than integer division. `NULLIF` protects an empty denominator without inventing a zero rate. Averages ignore null durations, which is intentional because ineligible durations remain null.

Then explain `02_service_performance.sql`: order valid durations within service, assign ranks, calculate the percentile position `1 + (N - 1) × p`, and interpolate between its bounding ranks. This matches the continuous percentile convention used by pandas and the proposed Power BI measure. The SQL is more detailed because standard SQLite does not include that percentile aggregate by default.

For the model, explain that dimensions provide unique labels for grouping while the fact table stores one row per request and its derived metrics. A created-date relationship answers intake questions. A separate inactive closure-date relationship answers closure-month questions only when explicitly activated.

## Five-minute demonstration

1. State scope and show the actual field dictionary.
2. Show the raw counts and the primary-cohort reconciliation.
3. Open one flag conflict and explain its treatment.
4. Run the headline SQL and show service median/P90 differences.
5. Present one evidence-supported recommendation and the missing information needed to test it.

Relate this to your maintenance-operations experience through clear definitions, workload prioritization and status reconciliation. Keep prior professional achievements separate from the measured outcomes of this project.
