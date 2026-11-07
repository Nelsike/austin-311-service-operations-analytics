# November 7–8, 2026 review milestones

The first version is deliberately organized into reviewable stages. The local build completes the data foundation, SQL analysis, documentation and Power BI preparation. Native Power BI implementation remains separate.

| Stage | Deliverable | Current state | What you should be able to explain |
| --- | --- | --- | --- |
| Saturday 1 — Source and scope | Actual definitions, frozen source, 2025 cohort | Complete | One row is a request; creation year differs from fiscal year |
| Saturday 2 — Quality and KPIs | Missingness, conflicts, status map, duration rules | Complete | Closure is not verified resolution; duplicate reports differ from duplicate IDs |
| Saturday 3 — Reproducible analysis | Python pipeline, SQLite warehouse, SQL evidence | Complete | How the headline counts and percentile denominators reconcile |
| Sunday 1 — Power BI | Import tables, add relationships/measures, create report pages | Completed November 7 | Which date relationship each visual uses and how slicers affect metrics |
| Sunday 2 — Acceptance and presentation | Desktop checks, real screenshot, short project walkthrough | Desktop checks and actual exports complete; interview practice continues | Demonstrate filter behavior, limits and one operational recommendation |
| Sunday 3 — Publication | Review GitHub files and publish selected artifacts | Private v1.0 ready; public release and LinkedIn attachment pending review | Why large raw data stays out of ordinary Git commits and how to reproduce |

For the first collaborative review, read the `reports/data_quality.md` table and the KPI definitions in `docs/methodology.md`. Confirm you can explain the 73,690 → 69,149 reconciliation and why 18 open records are a status-verification task before they become a recovery-work estimate. Then move to the SQL and Power BI pages.

These are project milestones, not scheduled reminders or an assumption that background work will continue automatically.
