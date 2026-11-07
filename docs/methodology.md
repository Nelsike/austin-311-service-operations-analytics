# Analytical decisions

## Business question and population

Which service types account for reported demand, how long do requests take to reach a closed status, and which reported open records deserve follow-up?

Use the City of Austin's [Transportation and Public Works 311 dataset](https://data.austintexas.gov/d/38mr-dwji), not the citywide 311 dataset. The publisher filters departments to Transportation/Public Works and reports dates in Central Time. See the saved `data/raw/city_metadata.json` for the actual schema and descriptions captured for this project. The [federal catalog entry](https://catalog.data.gov/dataset/311-service-requests-austin-transportation-and-public-works) independently describes the scope and time zone.

The cohort includes records with `2025-01-01 00:00:00 <= Created Date < 2026-01-01 00:00:00` in Central Time. A late-December request remains included if it closes in 2026. Fiscal year and the year prefix in the request number do not select the cohort.

One source row represents one service request, not one resident, one incident, one field visit or one completed repair. The snapshot contains current published values, not a request's event history. Department and group are the assignments visible in this snapshot, not proven assignments at creation.

## Intake versus the primary analytical cohort

Retain every 2025-created record in the raw and fact tables. Count all of them as gross intake. Use `in_primary = 1` for the main operational comparisons: exclude records marked `Is Duplicate = 1` and the explicit `CancelledTesting` status. Preserve duplicate-marked requests for a separate demand and sensitivity analysis. They can represent additional reports of the same issue; they are not erroneous database duplicates.

Repeated request identifiers would be a different problem. The pipeline stops on missing or repeated IDs rather than selecting an arbitrary record. It checks for schema changes and invalid numeric/binary flags as well. Unknown statuses are retained and flagged, and the full build stops if they prevent the primary open/closed partition from reconciling.

## Status precedence and conflicts

| Published status | Analytical status | Primary eligibility |
| --- | --- | --- |
| Closed | Closed | Yes, unless duplicate flag is set |
| Duplicate (closed) | Closed | No when duplicate flag is set |
| Open | Open | Yes, unless duplicate flag is set |
| Duplicate (open) | Open | No when duplicate flag is set |
| CancelledTesting | Excluded | No |
| Any future/unrecognized value | Unknown | Review before publishing results |

The explicit status takes precedence over conflicting boolean flags. Preserve the flags as `source_*` columns and record disagreements in `quality_issues.csv`. An open request with a missing close date supports an open classification even when its source `Is Open` flag is zero. A testing record is excluded rather than interpreted as a normal closure. A closed status can count toward closure share while being ineligible for time calculations if its timestamp is missing or invalid. Open-with-close-date conflicts are flagged, not treated as a reliable historical transition.

## Closure is an administrative event

`Close Date` establishes the time a request was marked closed. The file has no independently verified completion event, work-order outcome, inspection result or customer confirmation. Therefore:

- Use **closure time**, **reported closed**, and **reported open backlog**.
- Verified resolution rate and repair completion time are unavailable.
- Do not interpret a very short closure as proof of a quick physical repair.
- `Response Days` has a broad publisher definition, but no first-response timestamp is provided. Retain it for context; do not present it as a validated first-response KPI.

The City’s [311 audit](https://services.austintexas.gov/edims/document.cfm?id=347362) also discusses problems with closing requests before the underlying issue is resolved. That contextual evidence does not establish the outcome of any particular record in this cohort.

## Time calculations and daylight saving

Parse the exact export format, `%Y %b %d %I:%M:%S %p`, after trimming whitespace. Treat local timestamps as `America/Chicago`, then convert them to UTC before subtracting. A calendar day crossing the spring clock change can contain 23 elapsed hours. One elapsed day means 86,400 seconds; these are not business days or a holiday-adjusted calendar.

Local timestamps in the repeated fall hour cannot be uniquely converted without an offset. Do not guess which occurrence applies. Keep affected requests in volume and status counts, flag them, and exclude them from calculations that need the ambiguous instant. Four primary closed requests in v1 are excluded from closure-duration and deadline denominators for that reason.

The fixed age cutoff for v1 is **November 7, 2026, 00:00 Central Time**. This is a declared reporting convention, not a certified extraction timestamp. Statuses are observed in the user's November 7 export. The cohort's close/update/status-change timestamps are checked against the cutoff; it is not used to reconstruct historical statuses. Preserve original local strings and UTC strings alongside derived durations. Never use `TODAY()` to silently change this snapshot's age metrics.

## KPIs and denominators

| KPI | Definition | Denominator and limitation |
| --- | --- | --- |
| Gross intake | All records created in calendar 2025 | Includes duplicate-marked and testing records; label explicitly |
| Primary requests | Nonduplicate, nontesting cohort records | Main population for service comparisons |
| Reported closed requests | Primary requests with mapped Closed status | Status-based; may lack a usable duration |
| Snapshot closure share | Reported closed / primary requests | Long-followed 2025 cohort observed in Nov 2026; not an annual productivity or resolution rate |
| Reported open backlog | Primary requests with mapped Open status | Only the 2025-created cohort; not TPW's all-years backlog |
| Median closure time | 50th percentile of `(closed_utc - created_utc) / 86400` | Only closed requests with valid, nonnegative elapsed times |
| P90 closure time | 90th percentile, continuous linear interpolation | Same eligible set as median; show eligible N |
| Mean closure time | Average valid closure time | Tail-sensitive context, not the headline |
| Closed by recorded deadline share | Valid closed requests with `close <= overdue_on` / deadline-eligible closed | Requires valid closure interval and recorded due timestamp at/after creation; not verified SLA compliance |
| Reported open past deadline | Primary Open requests with valid recorded due time before cutoff | Excludes missing/invalid due times; report their count if present |
| Open age | `(cutoff_utc - created_utc) / 86400` for primary Open | Snapshot age, not age since last staff action |
| Duplicate-marked share | Duplicate-marked requests / all nontesting intake | A request-reporting pattern, not necessarily avoidable demand |

Do not replace the per-record deadline with a blanket 30-day target. The publisher says the due date is usually within 30 calendar days, but actual targets vary by service. The current due timestamp may have been revised; deadline history is absent. Both closed-by-deadline numerator and denominator exclude ambiguous times.

## Missingness and transformation policy

Blank or whitespace-only fields are missing. Literal strings such as `NA` are not automatically converted to null. Do not impute closure dates, deadlines or coordinates. A missing close date can be expected for an open request, so distinguish structural missingness from a broken record.

Trim surrounding whitespace; parse comma-separated numeric values such as fiscal year `2,025`; preserve request IDs as text. Keep department/group label variants separate because a verified organizational crosswalk is unavailable. Service-description trimming is an auditable transformation, not fuzzy category matching. Extract longitude and latitude from the supplied WKT point; do not mistake state-plane coordinates for longitude and latitude. Spatial coverage does not measure equal access to reporting channels.

## Interpretation limits

Closed-only summaries exclude still-open durations and therefore can understate total eventual cycle times. The cohort has different follow-up lengths across creation months. Do not compare month-level closure shares as if they had equal observation windows. A future extension could use fixed 7/30/90-day closure windows or survival methods, with their assumptions stated.

Single-snapshot data does not support a defensible historical month-end backlog series, reopen counts, work hours, staffing utilization, cost savings, causal channel effects or all-city geographic need. Even a creation/close-date approximation can misstate history when requests reopen. The backlog page therefore displays the observed snapshot only. Use separate intake-month and closure-month visuals, and label each explicitly.

Service types have different work content and targets. Compare similar services, show volume and deadline context, and frame bottleneck explanations as hypotheses to investigate. No operational intervention or realized impact has been measured by this portfolio project.
