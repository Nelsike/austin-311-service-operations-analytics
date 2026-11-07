-- One row per request CREATED in 2025, primary = nonduplicate and nontest.
-- Snapshot closure share, not a 2025 annual closure rate or verified resolution.
SELECT COUNT(*) AS primary_requests,
       SUM(is_closed) AS closed_requests,
       SUM(is_open) AS open_backlog,
       1.0*SUM(is_closed)/NULLIF(COUNT(*),0) AS snapshot_closure_share,
       SUM(valid_closure) AS duration_eligible_closed,
       AVG(closure_days) AS mean_closure_days,
       SUM(valid_deadline_closure) AS deadline_eligible_closed,
       1.0*SUM(closed_by_deadline)/NULLIF(SUM(valid_deadline_closure),0) AS closed_by_recorded_deadline_share,
       SUM(open_past_deadline) AS open_past_recorded_deadline
FROM v_primary_requests;
