# Austin 311 Service Operations — findings and recommendations

**Population:** requests created in calendar 2025 and published in the user's November 7, 2026 export of dataset `38mr-dwji`. **Primary cohort:** nonduplicate, nontesting requests. **Age cutoff:** 2026-11-07T00:00:00-06:00.

## What the evidence establishes

| Measure | Observed result | Eligible population |
| --- | --- | --- |
| Gross 2025 intake | 73,690 | All 2025-created records |
| Duplicate-marked intake | 4,540 (6.16%) | All nontesting intake |
| Testing record | 1 | Retained, excluded from primary |
| Primary requests | 69,149 | Nonduplicate, nontesting |
| Reported closed | 69,131 | Primary |
| Reported open | 18 | Primary, observed statuses |
| Snapshot closure share | 99.974% | Closed / primary |
| Median administrative closure | 4.66 hours (0.194 days) | 69,127 eligible closed |
| P90 administrative closure | 9.03 days | Same eligible closed set |
| Mean administrative closure | 4.40 days | Same eligible closed set |
| Closed by recorded deadline | 67,120 / 69,127 (97.10%) | Valid closed intervals and recorded deadlines |
| Verified resolutions | Unavailable | No verification/outcome field |

The 99.974% figure describes a mature cohort after substantial follow-up. It does not prove that physical issues were fixed or measure the department's closure performance during calendar 2025. Four primary closed requests have ambiguous Central Time creation timestamps and remain in the closed count while being excluded from elapsed-time metrics.

## 1. Verify the reported backlog before assigning recovery work

All 18 primary requests still marked Open are past their recorded deadline. Their ages at the fixed cutoff range from 550.4 to 605.4 days. 16 of 18 were created on May 1–5, 2025; all show last-update dates no later than May 2025. Two conflict with the source open flag. The clustering and old update dates suggest checking publication or workflow history; the export alone cannot establish a system defect or confirm that the underlying work is unfinished.

**Proposed action:** the operations/data owner reviews these 18 IDs against the live request system and any linked work orders. Record whether each is genuinely open, already completed, transferred or incorrectly published. Fix confirmed status/flag issues through the normal source-system process. Measure verified backlog and reconciliation exceptions afterward. Do not claim an achieved backlog reduction.

Evidence: `04_open_backlog.csv`, `06_quality_checks.csv`, and `quality_issues.csv`.

## 2. Investigate long closure intervals within comparable services

Road Markings/Striping — Maintenance has 1,018 primary requests, median 53.78 days and P90 77.95 days. Traffic Sign New has 1,266 requests, median 33.26 days and P90 72.95 days. Yet striping's recorded-deadline closure share is 99.71%; a long duration alone is not evidence of a missed target. Sign New's corresponding share is 84.98%.

**Proposed action:** service managers sample long-duration cases and compare planning, inspection, batching, material availability and target-setting rules. These are candidate explanations, not observed causes. Establish service-specific baselines before testing a scheduling change. Track eligible N, median/P90 and recorded-deadline share together. No staffing increase, savings estimate or causal claim is supported by the current file.

Evidence: `02_service_performance.csv` and `08_workflow_diagnostics.csv`.

## 3. Treat duplicate-marked requests as a separate demand signal

There are 4,540 duplicate-marked requests, 6.16% of nontesting intake. Traffic Signal — Maintenance accounts for 3,263 of them out of 11,738 total signal-maintenance reports (27.80%). Its primary count is 8,475. A report is not necessarily an independent incident, and the data lacks a parent-request key to reconstruct incident groups.

**Proposed action:** inspect a sample of duplicate signal reports to understand whether repeated reporting, routing practices or another process explains the designation. Consider clearer resident status updates only if that review supports the idea. Preserve the additional reports as a demand indicator rather than deleting them or promising a preventable workload reduction.

Evidence: `05_duplicate_sensitivity.csv` and `09_duplicate_mix.csv`.

## 4. Separate administrative workflows from field-service claims

Lane/Road Closure Notification has 2,250 primary requests and both median and P90 equal to zero elapsed days. Activate/Deactivate Work Zone has 502 and the same pattern. These are timestamp observations, not proof of instantaneous field work. The all-service median also reflects the volume of fast parking and signal workflows.

**Proposed action:** agree with service owners which request types represent notifications, triage, investigation and repair. Create a verified workflow crosswalk in a later version. Publish closure metrics under their actual meaning, and add work-order completion/inspection evidence before introducing a verified resolution KPI.

Evidence: `08_workflow_diagnostics.csv` and the official field definitions.

## Demand context and limits

The highest primary intake month is 2025-05 with 7,062 requests. One year is insufficient to establish recurring seasonality. Channel and service mix, differing targets and unequal follow-up complicate comparisons. This snapshot does not establish historical month-end backlog, capacity, all-years TPW backlog, costs or service equity. All recommendations above are proposals; none has been implemented or evaluated in this project.
