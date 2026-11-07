# Power BI Desktop validation

Status: **Passed for the frozen v1 source snapshot on November 7, 2026**.

| Check | Result | Evidence |
| --- | --- | --- |
| CSV import and types | Pass | 73,690 fact rows; typed keys, flags, dates and durations |
| Relationships/date table | Pass | Six relationships; zero orphan-key sets; complete date dimension marked Time |
| DAX compiles | Pass | Report loads and seven model query scenarios execute |
| Headline counts and durations | Pass | 69,149 primary; 69,131 closed; 18 open; median 0.1940856481 days; P90 9.0269490741 days |
| Service and month selections | Pass | Actual UI: May 7,062 requests/16 open; traffic-signal maintenance 8,475 requests/1 open; clearing restores full totals |
| Closure-date role | Pass | DAX closure-month totals agree with SQL, including closures in 2026 |
| Blank duration/empty backlog handling | Pass | Four ambiguous creation instants excluded from durations; parking-enforcement selection shows zero open and an empty table |
| Save/reopen/refresh | Pass | Imported, refreshed, applied, saved, closed and reopened; headline and interaction checks repeat successfully |
| Actual dashboard export | Pass | Native three-page PDF exported from Desktop and all pages rendered and visually reviewed |

Power BI Desktop version: **2.159.1231.0 64-bit (October 2026)**. Validation date: **November 7, 2026**.

Evidence: `reports/powerbi_actual_results.json`, `reports/powerbi_validation.json`, `powerbi/validation_queries.json`, the native project in `powerbi/desktop/`, and `reports/dashboard-1.png` through `dashboard-3.png`. Public export images contain the report canvas, not account details or application chrome.

The static PDF captures each table's visible viewport; the interactive report allows scrolling through all 43 services and 18 primary open records. There is no dedicated quality-record drill-through page in this first release; request-level exceptions remain in the local analysis outputs. No cloud report was published and no operational intervention was implemented.
